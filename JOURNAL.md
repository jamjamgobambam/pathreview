## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now, PathReview's retriever ranks chunks using only vector similarity and keyword overlap scores. This means the final context sent to the generator may include chunks that match on surface keywords but aren't actually relevant to the user's query. The fix is to add an optional re-ranking pass that calls a smaller LLM to score each chunk's relevance before the top-k are handed to the generator. This lives in the rag/retriever module, primarily in a new reranker.py file and integration with hybrid.py. A successful implementation would improve answer quality by filtering out false-positive retrievals.

**Issue selection reasoning (Is this right for me?):**
I can explain the issue without looking at it: the retriever currently ranks chunks by vector and keyword scores alone, but that misses relevance nuance that only an LLM can catch. The fix adds an optional reranker step before generation. I found the relevant files (rag/retriever/hybrid.py exists, reranker.py is new) and read the retriever logic enough to sketch a plan. I checked the test directory and found existing retriever tests I can mirror. I chose Tier 3 because I have prior, though minimal, experience with RAG pipelines and LLM APIs, and the scope is contained to one new module plus one integration point. The 7-10 hour estimate fits within the two-week implementation window given my schedule. No blockers or dependencies on other issues.

**Branch name:** feat/34-setup-&-short-description

**Branch link:** https://github.com/Modeste01/pathreview/tree/feat/34-setup-%26-short-description

**Setup confirmation:** [x] App runs locally at localhost:5173
![alt text](image.png)
![alt text](image-1.png)

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Modeste01/pathreview/commit/80c9bfa

**Reproduction summary:**
Two-part reproduction. First, a structural test confirms the reranker module does not exist: importing `ChunkReranker` from `rag.retriever.reranker` raises ImportError, and `HybridRetriever.__init__` has no `reranker` parameter. Second, a behavioral test simulates what happens without a reranker: given a query like "What frontend frameworks does this candidate use?", the retriever returns chunks scored by keyword overlap alone. A chunk about "Flask REST API framework" (backend, not frontend) scores higher than a chunk about Vue.js because it has a stronger keyword match on "framework." Without an LLM to judge actual relevance, these false positives stay in the top results and get passed to the generator as context.

**PLAN.md link:** https://github.com/Modeste01/pathreview/blob/feat/34-setup-%26-short-description/PLAN.md

**Walkthrough video (recommended):** https://youtu.be/pZt-e1viPQE

**Blockers or open questions:**
Need to decide which LLM to use for reranking (GPT-3.5-turbo is cheap and fast, but a local model would avoid API costs in tests). Also need to confirm whether batching all chunks in one prompt or scoring them individually gives more reliable results.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks 1 and 2 from PLAN.md. Created `rag/retriever/reranker.py` with the `ChunkReranker` class that scores chunks in batches using an LLM, handles fallbacks on API errors or malformed responses, and filters by a configurable relevance threshold. Integrated it into `hybrid.py` as an optional `reranker` parameter so existing behavior is unchanged when no reranker is passed. Updated `rag/retriever/__init__.py` to export the new classes. Rewrote the test file with 9 unit tests covering normal reranking, top-k limits, API failures, malformed JSON, and the integration with HybridRetriever both with and without a reranker.

**Next steps:**
Sub-task 3: define the scoring prompt template (mostly done, lives in reranker.py already but may refine wording). Sub-task 5: add environment variable config to enable/disable reranking and set the model. Then open the PR and fill in Check-in 2.

**Blockers:**
None right now. Went with batched scoring (all chunks in one prompt) which resolved the earlier open question.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/452

**Branch:** `feat/34-setup-&-short-description`

**What you built:**
Implemented an optional LLM-based re-ranking step for the RAG retriever. The `ChunkReranker` class takes candidate chunks from the hybrid retriever, sends them to a smaller LLM in batches to score relevance (0-10), filters by a configurable threshold, and returns only the truly relevant chunks to the generator. It integrates into `HybridRetriever` as an opt-in parameter and falls back gracefully on API errors.

**Tests added or updated:**
`tests/unit/test_reranker.py` — 9 tests covering: module importability, HybridRetriever integration (with and without reranker), reranking by LLM score, top-k enforcement, API error fallback, and malformed JSON handling.

**Self-review confirmation:** [x] make check passes (no new errors; 162 pre-existing ruff errors in other files)  [x] make test-unit passes (no new failures; 53 pre-existing failures in other test files)

**Draft PR feedback received from:** [TO BE FILLED]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
stephanyTF reviewed PR #452. Positive notes: each section was thoroughly filled in and clear, and the design choice explanations were thoughtful. Two suggestions: (1) the integration test checkbox should be marked since I wrote tests covering integration with HybridRetriever, even though there's no formal integration test infrastructure; (2) it would help to list steps for running the reranker manually with test inputs to verify it works end-to-end.

**How you responded:**
Fair points on both. The integration checkbox was misleading. I do have tests that verify the reranker works inside HybridRetriever (not just in isolation), so that box should have been checked. On the manual testing steps, I didn't include those because the feature is toggled by env vars and there's no CLI entrypoint to run the retriever standalone. But I could add a short "how to verify locally" section to the PR description showing the env vars to set and a sample query to try.

---

### Reflection

**What was harder than you expected?**
Error handling and fallback logic. The core feature (send chunks to an LLM, get scores back) took maybe an hour. But then I spent three times that figuring out what to do when the LLM returns garbage JSON, when the API times out mid-batch, or when every chunk scores below threshold. I also didn't expect to fight pre-commit hooks that fail on code I never wrote. There are pre-existing mypy errors in `keyword_search.py` and `vector_store.py` that block commits touching any file in that module, which meant I had to skip mypy selectively and document why.

**What did you learn about working in a large codebase?**
You can't just drop code in. The project has conventions (conventional commits, branch naming, pre-commit hooks, specific test patterns) that took time to learn and follow. I also learned that reading existing code is the real work. Before writing `reranker.py` I had to understand how `hybrid.py` scores chunks, what format the generator expects, and how the test suite mocks external calls. In my own projects I skip that step because I already know everything. Here I couldn't.

**How did AI tools help — and where did they fall short?**
AI was great for scaffolding: generating the initial test structure, drafting the PLAN.md, and writing boilerplate like the config dataclass. It also helped me navigate the codebase faster (finding which files import what, tracing data flow). Where it fell short: it couldn't tell me whether my reranker actually improves retrieval quality in practice. That needs real queries against real data, and no amount of unit tests or LLM-generated code substitutes for running it end-to-end with actual resumes. I also had to manually verify that pre-commit failures were pre-existing and not caused by my code.

**What would you do differently if you started over?**
I'd lead with the behavioral reproduction in Week 8 instead of the structural one. Showing "this module doesn't exist" is obvious and tells the grader nothing. Showing a false positive where a backend chunk outscores a frontend chunk on a frontend query actually demonstrates why the feature matters. I'd also spend more time on the scoring prompt wording earlier. The prompt template in `reranker.py` works, but I think better instructions to the LLM would produce more consistent scores across different chunk lengths.

**What are you most proud of from this module?**
The batched scoring design. Instead of one API call per chunk (which would be slow and expensive), I batch 10 chunks into a single prompt and get all scores back at once. It's a small architectural choice but it makes the feature actually usable in production rather than just a proof of concept. The whole thing is opt-in via environment variables, so it doesn't break anything for anyone who doesn't want it.
