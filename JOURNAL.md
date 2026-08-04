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


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in before the end of the week. The PR is open at https://github.com/ascherj/pathreview/pull/[UPDATE WITH PR NUMBER].

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Getting the mocks right was harder than I expected. I assumed mocking the vector store would just mean swapping out `query()`, but `HybridRetriever._get_all_chunks()` also calls `get_collection()` and then calls `.get()` on the returned collection object to build the keyword index. That second layer of the mock chain was not obvious from reading the public interface — I had to trace through the source to find it. If I had missed it, the keyword indexer would have silently indexed nothing and the test would have passed for the wrong reason.

The other thing that caught me was the environment issue. Running pytest outside the project's virtualenv pulled in a completely different Python environment and the import failed immediately on `structlog`. That kind of setup problem is easy to overlook when you're focused on the code itself.

**What did you learn about working in a large codebase?**
You can't just read the public interface and assume you know what a class does. The real behavior is in the private methods, and those are what you have to understand before you can write a test that actually exercises the code rather than just passing around it. In my own projects I know every line, so I never have to do that kind of tracing. Here I had to read `hybrid.py`, `keyword_search.py`, `vector_store.py`, and `output_parser.py` carefully before I could write a single assertion with confidence.

I also noticed that the existing unit tests had a lot of pre-existing lint errors that nobody had fixed. In a real open source project that would be a signal to not introduce new ones, but also not to take on fixing unrelated issues in the same PR. Keeping the scope tight matters.

**How did AI tools help — and where did they fall short?**
AI was useful for moving fast on things I already understood — structuring the test classes, writing the fixture data, and drafting the PR description. It was also helpful for catching the `collections.abc` import issue before I pushed.

Where it fell short was anywhere that required actually understanding the codebase. The mock chain for `HybridRetriever` required reading the source and reasoning about what would happen at runtime. AI can suggest a pattern but it can't tell you whether that pattern matches what the real code actually does. I had to verify that myself.

**What would you do differently if you started over?**
I would read the source files for all three pipeline stages before writing any test code, not partway through. I started writing the retrieval tests before I fully understood how `HybridRetriever` used the vector store internally, and I had to go back and fix the mock setup. Reading first would have saved that back-and-forth.

I would also confirm the virtualenv situation on day one. The wrong environment issue was a simple fix but it was confusing in the moment.

**What are you most proud of from this module?**
The edge case tests. It would have been easy to write one happy path test and call it done. Instead the test suite covers empty retrieval, malformed JSON from the LLM, and zero scores when there are no chunks to evaluate. Those cases are the ones that actually catch regressions, and writing them required understanding the fallback behavior in `output_parser.py` and `EvalSuite` well enough to know what to assert. That felt like real contribution work, not just going through the motions.
