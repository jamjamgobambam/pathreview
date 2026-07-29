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
