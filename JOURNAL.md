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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review feedback was received prior to the deadline.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Dealing with the project's strict continuous integration (CI) standards was surprisingly difficult. I encountered multiple failures from the `ruff` and `black` pre-commit hooks due to strict line-length limits (E501) and specific formatting rules. It forced me to pay much closer attention to Python styling conventions before committing, rather than just focusing on whether the logic worked.

**What did you learn about working in a large codebase?**
I learned the importance of Dependency Injection when extending an existing system. Instead of hardcoding API keys and OpenAI clients deep inside the `HybridRetriever`, I passed the `LLMReranker` in as an optional argument. This kept the retrieval logic modular and decoupled from the LLM configuration, which is crucial in a large codebase to prevent components from becoming tightly tangled.

**How did AI tools help — and where did they fall short?**
AI was incredibly helpful for writing the unit tests, specifically setting up the `unittest.mock.Mock` to simulate deep nested API responses (`mock_client.chat.completions.create.side_effect`). However, AI fell short initially when it tried to write code for me before I was ready, taking away my opportunity to learn the structure myself. I had to explicitly instruct it to guide me conceptually instead of just giving me the answers.

**What would you do differently if you started over?**
If I were to start over, I would explore using a dedicated embeddings/reranking model (like Cohere's Rerank API) instead of a general-purpose LLM like `gpt-3.5-turbo`. While asking an LLM to score chunks 1-10 works, a specialized reranking model would likely be much faster, cheaper, and wouldn't require me to parse raw text output with regular expressions.

**What are you most proud of from this module?**
I am most proud of successfully mocking the OpenAI API in my unit tests. It felt great to see the test pass and prove that my reranker was correctly re-sorting the chunks, all without actually making a single network call or costing any money.