## Solution plan

**Issue:** Implement a caching layer for repeated identical portfolio queries — https://github.com/ascherj/pathreview/issues/32

### Understand

Submitting the same profile twice runs the full review pipeline twice and leaves
two entries in the user's review history.

The submit path never checks for prior work. `POST /reviews`
(`api/routes/reviews.py`, `create_review_endpoint`) calls `create_review()` in
`core/services/review_service.py`, which unconditionally inserts a new
`Review(status="pending")` row, then queues `process_review()` as a background
task. `process_review()` runs ingestion, agent orchestration, RAG
retrieval/generation, and safety checks from scratch every time — nothing keys
off whether the profile's content has changed since the last completed review.

- **Expected:** resubmitting a profile whose content is unchanged returns the
  already-completed review immediately, with no new pipeline run and no
  duplicate history entry. If the profile's content has changed, a fresh review
  is generated.
- **Actual:** every submit creates a new review row and re-runs the entire
  pipeline, regardless of whether anything changed.

Cache-hit contract: on a hit, return the existing review — same review ID, no
new row. This matches the issue text ("return the stored review when nothing
has changed") and directly fixes the duplicate-history complaint.

One subtlety: the request body only carries `profile_id`, so "identical input"
must mean the *content* of the `Profile` row (`github_username`,
`portfolio_url`, `resume_text`, `resume_filename`), not the request itself. The
cache key is a hash of those fields.

### Map

- `core/services/review_service.py` — `create_review()` gains the cache lookup;
  a new helper computes the profile content hash; `process_review()` stores the
  hash on the review when processing starts. Functions touched here also gain
  type annotations: the repo's pre-commit mypy hook enforces
  `disallow_untyped_defs`, which this module does not yet satisfy.
- `core/models/review.py` — new nullable `content_hash` column (indexed) on
  `Review`. The completed review row in Postgres *is* the cached value; the
  hash is how we find it.
- `alembic/versions/` — new migration `003` adding `content_hash` to `reviews`.
- `api/routes/reviews.py` — `create_review_endpoint` only queues
  `process_review` when the service created a fresh review (cache miss).
- `core/models/profile.py` — read-only; source of the fields being hashed.
- `tests/unit/test_review_service.py` (or a new sibling test file) — failing
  tests written first, defining the contract above.

### Plan

1. **Reproduce and pin the contract with failing tests.** Reproduce live:
   submit the same profile twice via `POST /reviews`, record the two distinct
   review IDs and duplicated history. Write unit tests asserting the desired
   behavior: (a) unchanged content → second submit returns the same review,
   (b) no new history row on a hit, (c) changed content → new review,
   (d) prior review not `complete` → no cache hit. Commit with the tests
   failing — this is the Week 8 reproduction commit.
2. **Add the cache key.** Write a pure helper (e.g. `compute_content_hash`)
   that canonicalizes the profile's content fields (stable field order,
   explicit handling of `None`) and returns a sha256 hex digest. Add the
   `content_hash` column to `Review` plus migration `003`.
3. **Cache lookup in `create_review()`.** Compute the hash from the profile,
   query for a `complete` review with the same `profile_id` and
   `content_hash`, and return it on a hit. On a miss, create the pending
   review with the hash stored, as today. Return a flag (or tuple) so the
   route knows whether to queue `process_review`. Annotate the signatures of
   the functions this step touches so the changes pass the pre-commit mypy
   gate (`disallow_untyped_defs`), which the module currently fails.
4. **Wire the route and verify invalidation.** Skip the background task on a
   hit. Editing any hashed profile field changes the hash, so the next submit
   misses and regenerates — confirm with the invalidation test from step 1.
5. **Verify end to end.** All step-1 tests pass, the full unit suite stays
   green, and a live double-submit returns the same review ID the second time
   with only one history entry.

### Inputs & outputs

- **Input:** the same `POST /reviews` request as today — `{profile_id}` plus
  the authenticated user. No API schema changes.
- **Output on cache hit:** the existing completed `Review` (same ID, status
  `complete`, sections populated), returned immediately; no background task,
  no new row.
- **Output on cache miss:** unchanged from today — new pending review,
  pipeline queued.
- **Schema change:** `reviews.content_hash` (nullable string, indexed) via
  migration `003`.

### Risks & unknowns

- **Storage choice:** the plan stores the hash on the `Review` row in Postgres
  rather than in Redis. Redis is running in the stack, but the cached value
  *is* a Postgres row — a Redis entry would be a second source of truth that
  can drift (and vanish on restart) while the review persists. Confirm this
  reasoning holds during implementation; revisit if reviewers expect Redis.
- **Concurrent submits:** two rapid submits of the same profile both miss
  (the first review is still `pending`/`processing`, not `complete`) and both
  run the pipeline. This is deliberately out of scope: concurrent review
  requests are their own issue (#82, "Concurrent review requests for the same
  profile can produce inconsistent results"), which prescribes a per-profile
  lock. This fix only dedupes against *completed* reviews.
- **Where the hash is computed vs. stored:** `create_review()` needs the
  `Profile` loaded to hash it; today it only receives `profile_id`. Need to
  confirm the profile fetch there doesn't conflict with the route's existing
  ownership checks.
- **Unit-test style:** existing tests mock the db session heavily; asserting
  "returns the same review" through mocks may pin implementation details.
  May need one test that fakes the lookup result rather than the SQL.

### Edge cases

- **Profile content changed between submits** — hash differs, must regenerate
  (the core invalidation case).
- **Prior review exists but is `failed` or still `processing`** — not a cache
  hit; a new review is created so the user isn't served a failure or blocked.
- **Profile with all content fields `None`** — hash of empty content is still
  a valid, stable key; two empty submits should still hit the cache.
- **Same content, different profile** — hash matches but `profile_id`
  differs; lookup keys on both, so no cross-profile (or cross-user) leakage.
- **Pre-existing reviews with `content_hash = NULL`** (rows from before the
  migration) — never match a lookup; first resubmit regenerates and caches.
