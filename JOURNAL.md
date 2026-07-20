# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [] Tier 2  [x] Tier 3

**Problem summary:**
The retriever currently ranks chunks purely by blending vector similarity and BM25 keyword scores, which are both mechanical signals that can rank a topically-close chunk above one that actually has the language the query needs. This issue adds an optional post-retrieval step where a smaller/cheaper LLM reads the query alongside each candidate chunk and assigns it a relevance score, letting semantic judgment re-order the candidates before the top-k are passed to the review generator. Right now there's no reranking at all — `HybridRetriever.retrieve()` returns its blended-score ranking directly with no LLM involved. A successful fix adds a new `LLMReranker` class (in a new `rag/retriever/reranker.py`) that scores and reorders a candidate pool, wires it into `HybridRetriever.retrieve()` as an optional parameter so existing behavior is unchanged when it's not configured, and falls back to the original ranking if the LLM call fails or returns malformed output. It touches `rag/retriever/hybrid.py` and adds the new reranker file alongside it.

**Branch name:** https://github.com/qixuan-code/pathreview/feat/34-llm-reranker-retriever

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

**Selection notes ("Is this right for me?" checklist reasoning):**

*Part 1 — Understanding the issue*
Paraphrased without re-reading: the retriever's ranking today is entirely score-based math (vector + keyword blend); this issue adds a smarter second pass where an LLM actually judges relevance before the generator sees the chunks. Confirmed the affected code by reading `rag/retriever/hybrid.py` in full (129 lines — vector query, keyword search, score blending, filtering, sort, truncation to `max_chunks`). Definition of done is concrete: before the fix, `retrieve()` always returns chunks ordered by blended vector/keyword score; after the fix, when a reranker is configured, the candidate pool gets re-scored and reordered by the LLM before truncation — and when no reranker is configured, behavior is byte-for-byte unchanged from today.

*Part 2 — Tier fit*
This one is genuinely borderline. The issue's own file list only touches `rag/retriever/`, which points to Tier 2, but the tier table separately calls out "RAG or agent modification" as Tier 3 typical scope, and this is exactly that. I'm logging it as Tier 2 based on what I actually found investigating it: the change is additive and optional — no existing caller needs to change, since nothing in `api/` or `agent/orchestrator.py` currently calls `HybridRetriever.retrieve()` at all — and there's an existing pattern to mirror rather than invent from scratch (`rag/generator/review_generator.py` for calling an LLM, `rag/generator/output_parser.py` for parsing its structured output). Flagging honestly, though: building a reference version of this myself took real design effort beyond just "add a function" — batching chunks into prompts, deciding fallback behavior on LLM failure, clamping malformed scores — so this sits at the upper edge of Tier 2 for me, not a quick one. Noting that now so it doesn't turn into a Week 9 surprise.

*Part 3 — Codebase readiness*
Read `rag/retriever/hybrid.py` end-to-end, including exactly where the blended results get filtered, sorted, and truncated — that's the single integration point a reranker needs to hook into. Read `rag/generator/review_generator.py` and `rag/generator/output_parser.py` as the closest existing precedent for "call an LLM, parse its response" in this codebase. Checked for existing tests covering this area and found none: no `tests/unit/test_hybrid.py`, and no test file exercises any LLM-calling component the way this reranker will need to be tested. Part of this issue is establishing that test pattern (mocking the OpenAI client) for the module, not extending an existing suite.

*Part 4 — Scope and time*
Still need to check the issue's comment thread and the cohort ledger's Claims count live before finalizing. On time: the issue's own estimate is 7–10 hours, and a dry-run reference build I did (reranker class + config + fallback handling + six test cases covering the mock path, reordering, LLM failure, malformed JSON, score clamping, and batching) took a comparable amount of focused effort once batching and failure handling are accounted for — so I'm treating 7–10 hours as realistic, not padded, and planning to spread it across both weeks rather than one sitting. Two things worth flagging as PR-description context, not blockers: (1) `HybridRetriever` isn't called anywhere in the running app yet, so this reranker will be correct and independently testable but won't visibly change what any user sees until something else wires the retriever into the app — a pre-existing gap I'm not taking on here; (2) there are two latent bugs nearby (`VectorStore.add_chunks()` doesn't match the real `Chunk` dataclass's fields, and `HybridRetriever` never calls `keyword_searcher.index()` before searching) that I'm noting but deliberately not fixing as part of this PR to keep scope disciplined. No "blocked by" references found on the issue itself.
