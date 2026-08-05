# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/38

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview builds a review by chaining several RAG stages together — retrieving the most
relevant profile chunks, reranking them, sending them to an LLM to generate the review
text, and parsing that text into structured feedback sections. Today each of those stages
is only exercised by its own isolated unit tests, and there is no single test that runs the
stages end-to-end. That gap means a regression at a *seam* between stages — for example a
shape mismatch between what the retriever returns and what the generator expects — could
pass every unit test while silently breaking the real flow. A successful fix adds an
integration test at `tests/integration/test_rag_pipeline.py` that drives a representative
query through the entire retrieval → rerank → generation → parsing path against the
deterministic mock LLM provider and asserts a well-formed review comes out, giving CI a
fast, offline regression guard for the whole pipeline.

**Selection reasoning ("Is this right for me?" checklist):**
- **Tier acknowledged / skill alignment:** This is a **Tier 2** issue (intermediate —
  requires cross-module understanding). That matches my comfort level: I'm comfortable with
  Python and `pytest` and can read across modules, so a test that spans the RAG package is a
  deliberate, appropriate stretch rather than an overreach.
- **Do I understand the issue?** Yes — it asks for one end-to-end test, using the existing
  mock LLM provider so results are deterministic (no live API, no cost).
- **Is the scope realistic?** Yes. The change surface is small and additive — a single new
  test file, **no production-code changes required** — while still touching multiple modules
  to read (`rag/` retriever/reranker/generator/parser, `core/config.py` for the mock
  provider, `tests/` conventions). That "read broadly, write narrowly" shape is exactly the
  Tier-2 intent and keeps risk low. The tracker's 4–6h estimate is realistic for one issue.
- **Blockers / dependencies?** None external — the mock provider means no keys or network.
  During setup I already located the pipeline stages and confirmed the pieces exist to wire
  together, so there are no unknown dependencies.
- **Why not Tier 1 / Tier 3?** Larger than a Tier-1 one-line fix (it requires understanding
  the whole pipeline), but well short of a Tier-3 architectural change (no design decisions,
  no schema/API changes).

**Branch name:** `test/38-rag-pipeline-integration-test`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Setup evidence (Week 7)

Environment stood up on Windows 11 following `docs/SETUP.md` (Docker services + Python venv
+ frontend). Captured 2026-07-21.

**Backing services healthy (`docker compose ps`):**
```
SERVICE   STATUS                    PORTS
db        Up (healthy)              0.0.0.0:5433->5432/tcp
redis     Up (healthy)              0.0.0.0:6379->6379/tcp
```
(Postgres is mapped to host port **5433** on Windows per SETUP.md, matching `.env`'s
`DATABASE_URL`.)

**Database migrated + seeded:**
```
alembic upgrade head  ->  ran migrations 001, 002 successfully
scripts/seed_db.py    ->  seeded 3 test accounts (user1..3@example.com)
```

**Frontend loads at http://localhost:5173 (the Week 7 requirement):**
```
$ curl -sI http://localhost:5173/
HTTP/1.1 200 OK
Content-Type: text/html

$ curl -s http://localhost:5173/ | grep -o '<title>.*</title>'
<title>PathReview - AI Portfolio Review Assistant</title>

# Vite dev server:  VITE v5.4.21  ready
```

**Backend API responds at http://localhost:8000:**
```
$ curl -s http://localhost:8000/
{"message":"PathReview API is running","version":"1.0.0"}   # HTTP 200

$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
200                                                          # Swagger UI
```

**Environment observations (pre-existing, not part of issue #38):**
- `GET /health` returns 503 due to two pre-existing bugs in `api/routes/health.py`, *not*
  actual outages (Postgres/Redis are up — migrations and seeding both succeeded against
  them): (1) the Postgres check runs a raw `"SELECT 1"` string instead of
  `sqlalchemy.text("SELECT 1")` (invalid under SQLAlchemy 2.0), and (2) the Redis check
  reads `settings.redis_host`, an attribute that does not exist on the `Settings` model
  (only `redis_url` is defined in `core/config.py`).
- The `chromadb/chroma:0.4.22` container image crashes on boot (`AttributeError: np.float_
  was removed in the NumPy 2.0 release`). Neither issue blocks the app from loading at
  `localhost:5173`, and both are outside the scope of issue #38.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/GurupavanSudhakar/pathreview/commit/6a3e495

**Reproduction summary:**
Issue #38 is a feature gap, not a crash, so "reproducing" it means confirming the gap is
real. Ran `.venv/Scripts/python.exe -m pytest tests/integration -v -m integration` and
got `no tests ran in 4.22s` (exit code 5, 0 items collected) — `tests/integration/`
contains only `__init__.py`. A repo-wide grep for `HybridRetriever`, `ReviewGenerator`,
and `parse_review_output` shows each class/function is referenced only inside its own
defining file (`rag/retriever/hybrid.py`, `rag/generator/review_generator.py`,
`rag/generator/output_parser.py`, plus `parse_review_output`'s own unit test) — nothing
in the codebase currently exercises retrieval → generation → parsing together, exactly
the seam-level coverage gap the issue describes.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** Not recorded — not part of the grade for this
milestone, per the course guidance for Week 8.

**Blockers or open questions:**
While mapping the pipeline for `PLAN.md`, found two divergences from the issue text
worth flagging for Week 9: (1) there is no reranking stage anywhere in `rag/` — the
issue's "retrieval → reranking → generation → parsing" phrasing doesn't match the
codebase, so the Week 9 test will cover retrieval → generation → parsing only; (2)
there's no real mock **LLM** (chat) provider — `core/config.py`'s `llm_provider` setting
is never branched on anywhere, and the only existing mock is `MockEmbeddingProvider`
(embeddings only). `ReviewGenerator` hardcodes a live `openai.OpenAI` client with no
injectable seam, so "mock LLM" will mean a test-side fake/monkeypatch of that client,
not a new production mock-LLM class. Details and rationale are in `PLAN.md`'s
Understand/Map/Risks sections.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five sub-tasks from `PLAN.md`'s "Plan" section are complete, and
`tests/integration/test_rag_pipeline.py` now exists as the first test in
`tests/integration/`:

- *Sub-task 1 (retrieval fixtures)* — a `retriever` fixture stands up `VectorStore`
  against a pytest `tmp_path` and seeds it through `VectorStore.add_chunks(...)` with
  embeddings from the existing `MockEmbeddingProvider`, then indexes a `KeywordSearcher`
  over the same chunks. No Docker Chroma container needed.
- *Sub-task 2 (fake LLM)* — a hand-written `FakeOpenAIClient` shaped like
  `client.chat.completions.create(...)`, installed by patching
  `rag.generator.review_generator.openai.OpenAI` (the name as imported in that module).
  Hand-written rather than a `MagicMock` because a `MagicMock`'s
  `.choices[0].message.content` is itself a `Mock`, which `parse_review_output` would
  quietly route through its plaintext fallback and hide real breakage.
- *Sub-task 3 (wiring)* — tests call `HybridRetriever.retrieve(...)` and feed the result
  straight into `ReviewGenerator.generate_full_review(...)`, which is the seam nothing in
  the codebase currently exercises (`core/services/review_service.py`'s
  `_run_rag_retrieval_generation` is still a stub returning canned data).
- *Sub-task 4 (assertions)* — covers the blended chunk contract, five parsed
  `FeedbackSection`s, appended `Sources:` citations, context and profile data actually
  reaching the prompt, zero-retrieval degradation, and a per-section LLM failure.
- *Sub-task 5 (marker)* — the class is marked `@pytest.mark.integration`;
  `pytest tests/integration -v -m integration` went from `no tests ran` (exit 5, 0
  collected) to 8 collected and passing in ~3.5s.

**Next steps:**
Run an adversarial review pass over the test before opening the PR — specifically
checking whether it would actually fail if a seam broke, rather than just passing — then
fill in the PR template, document the pre-existing `make check` / `make test-unit`
failures so it's clear this change doesn't add to them, and open the PR against
`ascherj/pathreview`.

**Blockers:**
No hard blockers, but three things in the codebase shaped the implementation and are
worth recording:

1. `HybridRetriever.retrieve()` computes `all_chunks = self._get_all_chunks(...)` at
   `rag/retriever/hybrid.py:50` and then never uses it — `keyword_searcher.index(...)` is
   not called anywhere in the retriever, so the keyword arm returns `[]` and blended
   scores cap at `vector_weight` unless the caller indexes the searcher itself. The test
   fixture does this explicitly.
2. `VectorStore.add_chunks(...)` reads `chunk.id`, `chunk.source_id`, `chunk.chunk_index`
   and `chunk.section`, but `Chunk` (`ingestion/chunking/base.py`) only defines `text` and
   `metadata` — no object in the repo satisfies the method. The test defines a minimal
   `StoredChunk` record for the seam rather than changing production code.
3. `generate_section` returns the *parser's* `section_name` and `_consolidate_feedback`
   de-duplicates on it, so a fake LLM returning one canned payload for all five calls
   collapses the review from five sections to one. The fake therefore answers under each
   requested section's own key, matching on the distinct opening wording of each prompt
   template.

Tooling note: `make` is not installed on this Windows machine and the venv's
`.venv/Scripts/pytest.exe` shim exits 1 with zero output even for `--version`, so the
Makefile recipes are run directly via `.venv/Scripts/python.exe -m {pytest,ruff,black,mypy}`
— the same commands `make test-unit`, `make test-integration` and `make check` invoke
(`Makefile:39-59`).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/881

**Branch:** `test/38-rag-pipeline-integration-test`

**What you built:**
An integration test that drives one query through the real RAG pipeline —
`HybridRetriever.retrieve()` → `ReviewGenerator.generate_full_review()` →
`parse_review_output()` — against a deterministic mock LLM, closing the seam-level
coverage gap in issue #38. Retrieval runs against a real Chroma `PersistentClient` on a
pytest `tmp_path` seeded with `MockEmbeddingProvider` embeddings, and generation is
isolated by patching `rag.generator.review_generator.openai.OpenAI` with a fake chat
client that answers per requested section, so the whole test needs no Docker, no network
and no API key.

**Tests added or updated:**
Added `tests/integration/test_rag_pipeline.py` (8 tests, the first content in
`tests/integration/`). No existing test files were modified. What the tests cover:

- `test_retrieval_blends_vector_and_keyword_scores` — retrieved chunks carry exactly the
  keys `id/text/metadata/score/vector_score/keyword_score`, `score` equals
  `0.7 * vector_score + 0.3 * keyword_score`, chunk metadata survives the Chroma
  round-trip with its literal values intact, and results come back score-descending.
- `test_min_score_threshold_filters_weak_matches` — the `min_score` cut-off is actually
  applied to blended scores, asserted in a way that does not depend on how vector
  similarity is derived from distance.
- `test_pipeline_produces_all_sections_with_citations` — the generator is asked for all
  five sections in template order, returns five distinct sections, and each one ends with
  the `Sources: …` citation line built from the retrieved chunks' `source_id`s.
- `test_json_response_parses_into_structured_section` — a fenced-JSON reply lands on the
  parser's structured branch, giving `confidence == 0.9` and parsed `suggestions`, rather
  than silently falling through to the plaintext branch.
- `test_prompt_carries_retrieved_context_and_profile_data` — every retrieved chunk's text
  and `Source:` line reaches the LLM prompt at the right position, along with
  `github_username`, `project_count`, and the configured model/temperature/max_tokens.
- `test_every_context_chunk_reaches_prompt_and_citations_cap_at_five` — `_format_context`
  includes all supplied chunks in order and `_add_citations` cites at most five sources,
  omitting the sixth.
- `test_empty_retrieval_still_generates_uncited_sections` — the case where retrieval
  returns no relevant chunks: the pipeline still produces all five sections and appends no
  citations instead of raising.
- `test_single_section_llm_failure_yields_placeholder` — when one section's LLM call
  raises, only that section degrades to the `Error generating <section>` placeholder with
  `confidence == 0.0`, and the other four are unaffected.

Each of these was mutation-checked: production code was temporarily broken (renaming the
`text` key, dropping chunk text from the prompt, removing citation appending, changing the
blend weights, removing the per-section `try/except`, mis-attributing `source_id`,
truncating context, disabling the `min_score` filter) and confirmed to make at least one
test fail, then reverted.

**Self-review confirmation:** [x] `make check` passes [x] `make test-unit` passes

Read as the course guidance defines it for a codebase with documented pre-existing
failures — my changes introduce no new failures. Measured before and after, with the
Makefile's own commands:

| Check | Before my change | After my change |
| --- | --- | --- |
| `ruff check .` | 182 errors | 182 errors (new file: clean) |
| `black --check .` | 52 would reformat, 58 unchanged | 52 would reformat, 59 unchanged |
| `mypy api/ core/ ingestion/ rag/ agent/ safety/` | 5 errors in 4 files, exit 2 | identical (`tests/` is not in scope) |
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 53 failed, 375 passed — identical set |
| `pytest tests/integration -m integration` | no tests ran, exit 5 | 8 passed |

The 53 failing unit tests and 182 lint errors are pre-existing on `main` and untouched by
this branch; the failing-test names are byte-for-byte identical before and after.

**Draft PR feedback received from:** Carlton Tam — flagged that the first draft asserted an
exact retrieved-chunk count, which only passed because `VectorStore.query` converts cosine
distance with the euclidean formula `1 / (1 + distance)`, meaning a fix to that bug would
have broken the test; also that `keyword_score > 0` relied on `rank_bm25`'s negative-IDF
epsilon floor, that a `source_id` mis-attribution would have slipped through a
`startswith("repo_")` check, and that context truncation past the first chunk was
unasserted. All four were addressed in commit `d45627d` before the PR was opened.
