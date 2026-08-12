## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current RAG retriever relies solely on vector and keyword similarity for ranking documents. This issue proposes adding an LLM-based re-ranking step to evaluate and score the relevance of retrieved chunks before they are sent to the generator. Implementing this feature in the `rag/retriever` component will improve the overall quality and accuracy of the context used for generation.

**Branch name:** feat/34-llm-reranker

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hangolehai/pathreview/commit/866ac24

**Reproduction summary:**
I verified the codebase currently only uses vector and keyword similarity in `rag/retriever/hybrid.py`. I added a TODO comment in the `retrieve` method exactly where the new LLM re-ranking step needs to be inserted before it returns the `final_results`.

**PLAN.md link:** https://github.com/hangolehai/pathreview/blob/feat/34-llm-reranker/PLAN.md

**Walkthrough video (recommended):** [Skipped for now]

**Blockers or open questions:**
None at the moment. The plan is solid and I understand where the changes need to be made.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have fully implemented the LLM re-ranking feature for Issue #34. I created the `LLMReranker` utility class in `rag/retriever/llm_reranker.py` and successfully wired it into `HybridRetriever.__init__` and `HybridRetriever.retrieve`. 

**Next steps:**
Finish setting up tests and open a draft PR for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/543

**Branch:** `feat/34-llm-reranker`

**What you built:**
I built an `LLMReranker` class that intercepts the search results from the `HybridRetriever`. It takes the retrieved chunks, prompts OpenAI to score their relevance from 1-10 against the user's query, and then re-sorts the chunks so the generator gets the highest quality context first.

**Tests added or updated:**
I created a new test file `tests/unit/test_llm_reranker.py`. It uses `unittest.mock.Mock` to simulate OpenAI's API response and verifies that chunks are correctly re-sorted based on the mock LLM scores.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** N/A

## Week 10 — Iteration & Reflection

**Code Review Status:** 
No review feedback was received prior to the deadline, so no iteration was necessary.

**Final Project Reflection:**
For my open-source contribution, I tackled Issue #34, which required implementing an LLM-based re-ranking step for the application's Retrieval-Augmented Generation (RAG) pipeline. The existing system relied entirely on vector similarity and keyword matching (BM25), which often struggled to surface the most conceptually relevant document chunks. 

**What I Built & Why:**
I built an `LLMReranker` class that intercepts the blended results from the `HybridRetriever`. Rather than altering the core math of the vector/keyword search, the reranker takes the top retrieved chunks, prompts OpenAI to evaluate their relevance against the user's query on a scale of 1-10, and then re-sorts them. 

I specifically utilized **Dependency Injection** by passing the `LLMReranker` instance directly into the `HybridRetriever.__init__` method as an optional argument. I chose this design pattern because it decoupled the retrieval logic from the LLM configuration—the retriever doesn't need to know how to handle OpenAI API keys or manage timeouts. It simply asks, "If I have a reranker, use it." This made the codebase much easier to test and far more modular.

**Challenges & Testing:**
The most significant hurdle was ensuring my code met the project's strict continuous integration (CI) standards. I encountered failures from the `ruff` and `black` pre-commit hooks due to line-length limits (E501) and formatting inconsistencies. Fixing these forced me to pay much closer attention to Python styling conventions and how automated tools enforce them.

When writing unit tests for the feature, I had to ensure the test suite ran quickly and didn't rack up OpenAI API costs. I solved this by utilizing `unittest.mock.Mock` to simulate deep API responses (e.g., `mock_client.chat.completions.create.side_effect`), mapping specific mock scores to specific fake chunks.

**What I Would Do Differently:**
With full context now, if I were to build this again, I would explore using a dedicated, smaller embeddings model (like `bge-reranker` or Cohere's Rerank API) instead of a general-purpose LLM like `gpt-3.5-turbo`. While the LLM approach works, a specialized reranking model would likely be much faster and cheaper at scale, while reducing the need to parse raw text output with regular expressions.