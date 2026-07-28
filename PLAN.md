# Solution plan

**Issue:** Implement a caching layer for repeated identical portfolio queries —
https://github.com/ascherj/pathreview/issues/32 (Tier 2)

### Understand

**Root cause.** `process_review()` in `core/services/review_service.py` runs the
full review pipeline — ingestion → agent orchestration → RAG retrieval/generation
→ safety checks — on *every* invocation. Nothing keys work to the profile's
content, so when a user resubmits the same portfolio with no changes, the
expensive `_run_rag_retrieval_generation()` step (and everything before it) runs
again and produces an identical result at full compute/latency/LLM cost.

**Expected vs. actual.**
- *Expected:* Submitting an unchanged profile a second time returns the
  previously generated review quickly (a cache hit) without re-running the RAG
  pipeline. Changing any profile content produces a different hash and triggers a
  fresh generation.
- *Actual:* The pipeline runs in full every time. This is demonstrated by
  `tests/unit/test_review_cache_reproduction.py`, an `xfail(strict=True)` test
  showing `_run_rag_retrieval_generation` is called twice for two identical
  submissions (expected: once).

### Map

Files/functions I expect to touch:

- **`core/services/review_service.py`** — primary change.
  - Add a `compute_profile_content_hash(profile)` helper that hashes the
    content-bearing fields: `github_username`, `portfolio_url`, `resume_text`,
    `resume_filename` (SHA-256 over a canonical serialization).
  - In `process_review()`, before running the pipeline, look up a prior
    `complete` review with a matching hash; on hit, copy its `sections` /
    `overall_score` into the current review, set `status="complete"`, and return
    early. On miss, run the pipeline and persist the hash.
- **`core/models/review.py`** — add a nullable, indexed `content_hash`
  `String(64)` column so completed reviews can be looked up by hash.
- **`alembic/versions/<new>_add_review_content_hash.py`** — migration adding the
  `content_hash` column + index (`alembic revision`).
- **`core/services/cache.py`** *(new, optional fast path)* — a thin Redis wrapper
  keyed `review:cache:<hash>` using the existing `REDIS_URL` from `.env`/
  `docker-compose.yml`, with the Postgres `reviews` table as the durable fallback.
- **`tests/unit/test_review_cache_reproduction.py`** — remove the `xfail` marker
  once fixed; expand into positive/negative cache-behavior tests.
- **`tests/unit/test_review_service.py`** — add cases for hash computation and
  cache hit/miss.

### Plan

1. **Hashing.** Implement `compute_profile_content_hash(profile)` and unit-test
   that identical content → identical hash and any field change → different hash.
2. **Schema.** Add the `content_hash` column to the `Review` model and generate
   the Alembic migration; run `alembic upgrade head` locally to verify.
3. **Cache lookup on the write path.** In `process_review()`, compute the hash;
   query for an existing `complete` review with the same `content_hash` (scoped
   to the same `profile_id`) and, on hit, reuse its stored output and return
   before the pipeline. On miss, run the pipeline and save the hash.
4. **(Optional) Redis fast path.** Add `core/services/cache.py` and check Redis
   first, then Postgres, populating Redis on a DB hit — behind graceful
   fallback if Redis is unavailable.
5. **Tests + checks.** Convert the reproduction test to a passing assertion, add
   hit/miss/invalidation tests, and run `make check && make test-unit`.

### Inputs & outputs

- **Input:** a `Profile` (its content fields) plus the `review_id`/`profile_id`
  passed to `process_review()`.
- **Output / change:**
  - New: a deterministic content hash per profile submission.
  - Changed: `process_review()` short-circuits on a cache hit, writing the cached
    `sections` + `overall_score` to the new review and setting `status="complete"`
    without invoking the pipeline.
  - New DB column `reviews.content_hash` (indexed); optionally a Redis entry
    `review:cache:<hash>`.
  - Observable effect: `_run_rag_retrieval_generation` runs once across repeated
    identical submissions instead of once per submission.

### Risks & unknowns

- **What counts as "content."** If the hash omits a field that actually affects
  output (or includes volatile metadata like timestamps), the cache will either
  miss when it should hit or serve stale results. Mitigation: hash only the four
  content fields on `Profile`, canonically serialized; cover with tests.
- **Stale cache after upstream changes.** If ingested GitHub/portfolio data
  changes but the stored profile fields don't, the hash won't change and a stale
  review is served. Need to decide whether hashing profile fields is sufficient
  for this issue's scope (I believe it is, per the issue text: "if the portfolio
  hasn't changed") or whether ingested-source content must be included.
- **Migration safety.** Adding a column requires a working Alembic chain;
  `content_hash` must be nullable to backfill existing rows without breaking them.
- **Redis availability.** The Redis path must fail open (fall back to Postgres /
  recompute) so a Redis outage never blocks reviews. Unknown: is Redis already
  wired into a client anywhere, or do I introduce the first client? (Grep shows
  `REDIS_URL` in config but no Python client yet.)
- **Concurrency.** Two identical submissions racing in parallel could both miss
  the cache and both run the pipeline. Acceptable for this issue, but worth noting.

### Edge cases

- **First-ever submission (cold cache):** no prior review → miss → run pipeline,
  store hash. Must not error on the empty-lookup path.
- **Profile with all content fields null/empty:** hash must be stable and not
  raise (e.g. a profile with no resume, no GitHub, no portfolio URL).
- **A single changed character** in `resume_text` (or any field) → different hash
  → cache miss → fresh review.
- **Prior review exists but `status="failed"` or `"processing"`:** must NOT be
  served as a cache hit — only reuse `status="complete"` reviews.
- **Same content across different profiles/users:** cache lookup is scoped to the
  owning `profile_id` so one user never receives another user's cached review.
- **Redis down / unreachable:** fall back to the Postgres lookup and still
  produce a correct review.
