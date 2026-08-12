# PLAN.md — Issue #34: LLM Re-ranking Step

## Problem
`HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` ranks chunks
using only `vector_weight * vector_score + keyword_weight * keyword_score`,
filtered by a numeric `min_score` threshold. There is no step that checks
whether a chunk is actually semantically relevant to the query, so
chunks with high vector/keyword overlap but off-topic content can still
reach the generator.

## Approach
Add an optional `LLMReranker` that runs after `retrieve()` produces its
blended, filtered candidates. It prompts a smaller LLM to score each
candidate's relevance to the query, then returns only the top-k
re-ranked chunks. Off by default to avoid changing existing behavior.

## Files to change
- `rag/retriever/reranker.py` (new)
  - `LLMReranker` class with a `rerank(query: str, chunks: list[dict], top_k: int) -> list[dict]` method
  - Builds a prompt per chunk (or batched), calls the LLM, parses a relevance score
  - Sorts chunks by LLM score, returns top_k, preserving existing dict shape
    (`id`, `text`, `metadata`, `score`, plus new `llm_score`)
- `rag/retriever/hybrid.py`
  - Add `use_reranker: bool = False` and `reranker: LLMReranker | None = None`
    params to `HybridRetriever.__init__` or `retrieve()`
  - If enabled, call `reranker.rerank(query, final_results, max_chunks)`
    before returning

## Sub-tasks
1. Confirm existing LLM-call pattern used elsewhere in `rag/` (for
   consistent client/prompt style) before writing reranker.py
2. Implement `LLMReranker` with prompt template + score parsing + fallback
3. Wire optional call into `HybridRetriever.retrieve()`
4. Unit tests: mock LLM responses, verify sorting/filtering logic
5. Unit test: `retrieve()` calls reranker only when `use_reranker=True`
   and existing behavior is unchanged when it's `False`
6. Run `make check && make test-unit`

## Risks / edge cases
- Added latency from LLM calls per chunk — consider batching one prompt
  for all candidates instead of one call per chunk
- Malformed/unparseable LLM score output — needs a safe fallback
  (e.g. keep original blended score if parsing fails)
- Must not break existing callers of `retrieve()` — default off,
  same return shape
- `_get_all_chunks()` already fetches full collection for keyword search;
  reranker should only score the already-filtered `final_results`
  (≤ max_chunks), not all chunks, to control cost
