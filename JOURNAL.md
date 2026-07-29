## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [] Tier 2  [x] Tier 3

**Problem summary:**
The current retrieval pipeline ranks document chunks using a combination of vector similarity and keyword-based scores. Although this hybrid approach identifies potentially useful chunks, the highest-scoring results may not always be the most relevant to the user’s specific query. This issue will add an optional LLM-based re-ranking step that scores the retrieved candidate chunks for relevance before the final top-k chunks are passed to the generator. A successful implementation will preserve the existing retrieval behavior when re-ranking is disabled and use the LLM-produced relevance scores when the feature is enabled.

**Branch name:** `feat/34-llm-chunk-reranking`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes

I selected this issue because it involves a meaningful improvement to the project’s retrieval-augmented generation pipeline and aligns closely with the AI engineering concepts covered in this course. I can explain the expected before-and-after behavior: currently, chunks are ranked only by hybrid vector and keyword scores, while the completed feature will optionally use a smaller LLM to evaluate semantic relevance and reorder the candidates before generation.

The issue identifies a focused implementation area in `rag/retriever/`, including a new `reranker.py` file and changes to `hybrid.py`. However, it requires understanding how retrieval results are represented, how the existing LLM client is called, how top-k selection works, and how the generator receives its context. I will review those functions and the relevant test files before modifying the implementation.

The estimated effort is 7–10 hours, which is realistic for me to complete during Weeks 8 and 9. My initial plan is to implement a reranker abstraction, request structured relevance scores from the existing LLM client, sort the candidate chunks by those scores, preserve a fallback path when re-ranking is disabled or fails, and add tests using mocked LLM responses. I will also confirm through the issue comments and cohort ledger that I am comfortable with the number of other students working on the issue and that there are no unresolved dependencies.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [(https://github.com/mehakgupta9/pathreview/commit/1f3234e7d6207635d53f53290ebc9ff4561bc04e)]

**Reproduction summary:**
Since this is a feature-gap issue, I reproduced it by confirming — through code inspection — that the re-ranking step does not exist and locating exactly where it would live. Running `grep -rin "rerank"` across `rag/`, `core/`, `api/`, and `agent/` returns no matches, and `rag/retriever/reranker.py` is absent. Reading `HybridRetriever.retrieve()` confirms the gap: at `rag/retriever/hybrid.py:94` the candidate chunks are sorted purely by the blended vector+keyword `score` and the top-k are handed straight to the generator (`rag/generator/review_generator.py:39`), with no LLM relevance step in between. This documents that the highest-scoring chunks are chosen by a lexical/embedding proxy rather than judged for relevance to the specific query.

Reproduction steps (anyone can re-run these):
1. `grep -rin "rerank" rag/ core/ api/ agent/` → no results (feature absent).
2. `ls rag/retriever/reranker.py` → No such file or directory.
3. Read `rag/retriever/hybrid.py:92-104` → chunks ordered only by blended hybrid score, no LLM re-ranking.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** _(optional — add Loom link if recorded)_

**Blockers or open questions:**
- Whether to score each chunk with a separate LLM call or batch all candidates into one scoring prompt (latency/cost vs. simplicity), given the free `google/gemma-3-27b-it:free` model configured in `core/config.py`.
- Whether to construct the OpenAI client inside `LLMReranker` or inject it (leaning toward injection for testability, matching `ReviewGenerator`).
