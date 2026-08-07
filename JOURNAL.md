# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** [Issue #38 — Add an integration test that runs the full RAG pipeline against a mock LLM](https://github.com/ascherj/pathreview/issues/38)

**Issue title:** Add an integration test that runs the full RAG pipeline against a mock LLM

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview currently has unit tests for individual RAG components, but it does not have an integration test proving that the components work together as one complete pipeline. This means a problem in the connection between retrieval, reranking, generation, and output parsing might not be detected by the existing tests. The proposed test will send a representative query through the full RAG workflow while using the mock LLM provider instead of making a real external LLM request. A successful implementation will verify that every stage receives the expected input, produces the expected output, and returns a correctly parsed final result.

**Issue fit and selection reasoning:**
I selected this Tier 2 issue because it requires understanding how several RAG modules connect rather than changing only one isolated function. This is more challenging than a Tier 1 issue, but the scope is still manageable because the issue identifies one primary test file, `tests/integration/test_rag_pipeline.py`, and provides an estimated effort of four to six hours. Using the mock LLM provider should allow the test to run predictably without depending on an external API or consuming API credits. I am comfortable working with Python and pytest, and this issue will help me build experience tracing data across multiple modules in a larger codebase.

**“Is this issue right for me?” selection notes:**
The issue has a specific expected outcome: one integration test should exercise the complete RAG flow from retrieval through final parsing. The main deliverable is limited to the integration-test area, although I will need to read existing retriever, reranker, generator, parser, mock-provider, fixture, and unit-test code before implementing it. The issue does not require a production LLM connection because the mock provider will make the test deterministic and suitable for continuous integration. The four-to-six-hour estimate fits the Module 3 timeline, and I understand that the Tier 2 label reflects the need for cross-module investigation.

**Expected implementation file:** `tests/integration/test_rag_pipeline.py`

**Branch name:** `test/38-rag-pipeline-integration-test`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/drmitte7/pathreview/commit/14d7862ee37839ad64fa147b7c73ddee71905d19

**Reproduction summary:**
I reproduced the issue by confirming that the `tests/integration` directory contains only `__init__.py` and that `tests/integration/test_rag_pipeline.py` is missing. I also confirmed that PathReview has separate unit tests for RAG components but no integration test that runs retrieval, reranking, generation, and response parsing as one complete workflow.

**PLAN.md link:** https://github.com/drmitte7/pathreview/blob/test/38-rag-pipeline-integration-test/PLAN.md

**Blockers or open questions:**
I still need to confirm whether “reranking” in issue #38 refers to the score blending performed by `HybridRetriever`, the separate `RelevanceScorer`, or both. I also need to confirm whether the expected mock LLM approach uses an existing provider abstraction or patches the OpenAI-compatible client call in `ReviewGenerator`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I created `tests/integration/test_rag_pipeline.py` and implemented the main workflow from my solution plan. The test creates deterministic document chunks, indexes them for vector and keyword retrieval, runs a representative query through `HybridRetriever`, and verifies that the relevant result ranks first. It also replaces the external LLM request with a deterministic mock, confirms that retrieved context reaches the generation prompt, and verifies that the response is parsed into structured feedback. The targeted integration test passed successfully on repeated runs.

**Next steps:**
I will run `make check` and `make test-unit`, compare the results with the failures observed before implementation, and confirm that my change introduces no new failures. I will then open a draft pull request, request peer or mentor feedback, address relevant feedback, and complete Check-in 2 with the final PR link and verification results.

**Blockers:**
The targeted integration test has no current blockers. Mypy reports three pre-existing type errors in `rag/retriever/vector_store.py`, `rag/retriever/keyword_search.py`, and `rag/generator/output_parser.py`. These files were not modified by this contribution.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/586

**Branch:** `test/38-rag-pipeline-integration-test`

**What you built:**
I added `tests/integration/test_rag_pipeline.py`, which tests the full RAG workflow from retrieval and hybrid reranking through mocked LLM generation and structured output parsing.

**Tests added or updated:**
I added `tests/integration/test_rag_pipeline.py`. It verifies vector and BM25 retrieval, hybrid reranking, mocked LLM generation, prompt context, and structured output parsing. The targeted integration test passes.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

The full repository checks contain 182 pre-existing Ruff errors and 53 pre-existing unit-test failures. I reproduced the same results on `upstream/main`, confirming that this branch introduces no new failures.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was received on my pull request before completing this reflection. My PR remains open and ready for review, but no additional changes were requested.

**How you responded:**
Since no reviewer feedback was received, I did not need to make any additional code changes or responses. I left the pull request open and ready for future review.

---

### Reflection

**What was harder than you expected?**
The hardest part was not writing the integration test itself, but understanding how all of the existing RAG components connect together. For issue #38, I had to work with `VectorStore`, `KeywordSearcher`, `HybridRetriever`, `ReviewGenerator`, and the output parser so that `tests/integration/test_rag_pipeline.py` exercised retrieval, reranking, generation, and parsing as one workflow. Another challenge was distinguishing problems caused by my code from existing repository problems, especially when `make check` reported 182 Ruff errors and `make test-unit` reported 53 failing tests.

**What did you learn about working in a large codebase?**
I learned that contributing to an existing codebase requires much more attention to scope than working on my own project. Instead of fixing every problem I found, I needed to stay focused on issue #38 and avoid modifying unrelated production files just because they contained lint, type, or test failures. I also learned how important it is to understand the repository's Git workflow, including working on a dedicated branch, rebasing onto `upstream/main`, force-pushing safely with `--force-with-lease`, and keeping the pull request focused.

**How did AI tools help — and where did they fall short?**
AI tools helped me understand unfamiliar parts of the RAG pipeline, plan the integration test, interpret pytest and Git output, and work through commands for rebasing, committing, and preparing the pull request. AI was also useful for helping me structure the mocked LLM response so the test could run without making a real OpenAI API request. However, I learned that AI suggestions still have to be verified against the actual repository because assumptions about function signatures, existing tests, or project behavior may not always match the current code, so running the code and checking the real test output was essential.

**What would you do differently if you started over?**
If I started again, I would open the draft pull request earlier so there would be more time for peer or maintainer feedback before the deadline. I would also inspect the interfaces between `HybridRetriever`, `ReviewGenerator`, and the output parser earlier in the process before writing the integration test, which would make implementation more direct. I would continue using a before-and-after testing baseline because comparing my branch with `upstream/main` was very useful for proving that the existing 182 Ruff errors and 53 unit-test failures were not introduced by my contribution.

**What are you most proud of from this module?**
I am most proud that I completed a real open-source-style contribution from issue selection through planning, implementation, testing, documentation, and pull request submission. My integration test in `tests/integration/test_rag_pipeline.py` successfully exercises the RAG pipeline end to end using deterministic data and a mocked LLM, and the targeted test passes without requiring an external API call. I also became much more comfortable working with Git branches, upstream repositories, rebasing, test failures, and documenting technical decisions in a professional pull request.