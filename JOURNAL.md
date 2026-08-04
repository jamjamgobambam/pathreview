## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/38

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM #38

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that individual RAG components (retriever, generator, evaluator) each have unit tests, but there is no integration test that exercises the full pipeline end-to-end. Nothing is currently broken — the goal is to write a test that wires all components together against a mock LLM to verify they interact correctly as a whole. A successful fix would catch regressions that unit tests miss, such as data passing incorrectly between pipeline stages.

**Is this right for me? — Scope reasoning:**
This is a Tier 2 issue. It requires understanding how the RAG pipeline components connect, writing async pytest tests, and setting up mock LLM responses — but it does not require changing any production code. The scope is well-defined (one test file, one pipeline flow) and is achievable without deep knowledge of every subsystem. It is a good fit for getting familiar with the codebase before tackling a feature or fix issue.

**Branch name:** test/38-integration-test-for-the-whole-rag-pipeline

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/lynbergjean/pathreview/tree/test/38-integration-test-for-the-whole-rag-pipeline
**Reproduction summary:**
The integration test directory (`tests/integration/`) existed but contained only an empty `__init__.py` — no test exercised the full RAG pipeline. I added `tests/integration/test_rag_pipeline.py` with an `xfail` placeholder that raises `NotImplementedError`, confirming the gap is real and pinpointing exactly where the test needs to live.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
- Need to confirm whether `RelevanceScorer` and `FaithfulnessChecker` make any external calls before deciding if they need to be mocked in the integration test.
- Need to verify the exact JSON shape the mock LLM response must return so `output_parser.py` parses it into named sections rather than falling back to plaintext.


## Week 9 — Mid-week check-in

**Status:** Implementation complete, tests passing, PR being prepared.

**What I did:**
I wrote the full integration test in `tests/integration/test_rag_pipeline.py`. The test wires all three RAG pipeline stages together using mocked external dependencies so it runs completely offline with no API keys or running services needed.

The test is organized into four classes:
- `TestRetrievalStage` — verifies `HybridRetriever.retrieve()` returns a non-empty list of dicts with the right keys (`id`, `text`, `metadata`, `score`)
- `TestGenerationStage` — verifies `ReviewGenerator.generate_full_review()` returns a list of `FeedbackSection` objects with non-empty content and no duplicate section names
- `TestEvaluationStage` — verifies `EvalSuite.run()` returns scores between 0.0 and 1.0 and that `overall_score` equals the mean of the two component scores
- `TestFullRAGPipeline` — one end-to-end test that runs all three stages in sequence and checks the boundary contracts between them
- `TestEdgeCases` — covers empty chunk lists, malformed JSON from the LLM, and zero scores when retrieval returns nothing

To answer the open questions from Week 8: `RelevanceScorer` and `FaithfulnessChecker` do not make external calls, so they did not need to be mocked. The mock LLM response needed to be a JSON object where each top-level key maps to a dict with `content` and `suggestions` fields, which is what `_parse_json_output` in `output_parser.py` expects.

I also caught and fixed a lint issue in the test file: `Generator` was imported from `typing` instead of `collections.abc`, which ruff flags as UP035 in Python 3.11. Fixed before opening the PR.

**Blockers:** None. All 11 tests pass and the file is lint-clean.


## Week 9 — Submission check-in

**PR link:** https://github.com/ascherj/pathreview/pull/[UPDATE WITH PR NUMBER]

**What I'm submitting:**
A single new file, `tests/integration/test_rag_pipeline.py`, with 11 integration tests covering the full RAG pipeline. No production code was changed.

**Self-review against the bar:**
- The happy path works and is tested end-to-end
- Edge cases are covered (empty retrieval, malformed LLM output, zero scores)
- The test file is lint-clean (`ruff check` passes with zero errors)
- All 11 tests pass in under 2 seconds with no external dependencies
- The mock setup matches the real ChromaDB and OpenAI response shapes so the mocks are realistic, not just stubs that bypass the actual logic
- `make check` fails on the repo overall but all errors are in pre-existing unit test files that were already failing on `main` before my branch. My file introduces no new lint issues.

**What I learned:**
The trickiest part was getting the mock chain right for `HybridRetriever`. It calls `vector_store.get_collection()` to build the keyword index, and the returned collection object also needs to support `.get()` with a specific return shape. Getting that wrong would have caused the keyword indexing step to fail silently rather than raising an error, which would have been hard to debug. Reading the source carefully before writing the mocks saved a lot of time.
