## Solution plan

**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation — https://github.com/ascherj/pathreview/issues/34

### Understand

`HybridRetriever.retrieve()` ranks purely by `blended_score = vector_weight*vector_score + keyword_weight*keyword_score` — no semantic judgment. Confirmed in `tests/unit/test_hybrid.py`: `retrieve()` has no `reranker` param (`TypeError`), `rag/retriever/reranker.py` doesn't exist (`ModuleNotFoundError`), and the blend math alone can rank a chunk that merely *embeds* close to the query above one containing the exact language needed. Expected: an optional `LLMReranker` re-scores/reorders the candidate pool before truncation; behavior is unchanged when it's not configured or when it fails.

### Map

- `rag/retriever/reranker.py` (new) — `LLMReranker` class.
- `rag/retriever/hybrid.py` — add optional `reranker` param to `retrieve()`.
- `tests/unit/test_hybrid.py` — already reproduces the gap; extend to cover the wiring.
- `tests/unit/test_reranker.py` (to do) — isolated `LLMReranker` unit tests.

### Plan

1. `LLMReranker` class + config (model, API key, batch size), mirroring `ReviewConfig`.
2. Prompt + parse: score each chunk 0–1 from the LLM's JSON output; clamp and validate.
3. Fallback: any LLM error or malformed output → return the original ranking untouched.
4. Wire it in: optional `reranker` param on `retrieve()`, applied after filtering, before truncation to `max_chunks`.
5. Tests: unit-test `LLMReranker` in isolation (mocked client) + extend `test_hybrid.py` for the wiring itself (invoked when configured, no-op when not, fails safely).

### Inputs & outputs

**In:** query, filtered candidate chunks, reranker config. **Out:** same chunks reordered by LLM relevance (optionally with an `llm_score` field), truncated to `max_chunks` — identical to today's output when `reranker` is `None` or the call fails.

### Risks & unknowns

- Latency/cost per retrieval; batching strategy (one call vs. batched prompt) not yet decided.
- LLM output may be malformed — parsing must be defensive, not assume well-formed JSON.
- Nothing currently calls `HybridRetriever.retrieve()` in the app, so this can only be unit-tested, not verified end-to-end.
- Two adjacent latent bugs (`VectorStore.add_chunks()` field mismatch, `retrieve()` never calling `keyword_searcher.index()`) are out of scope but close enough to watch for in test fixtures.

### Edge cases

- Empty candidate pool.
- LLM returns scores for only some chunks → missing ones keep their original blended score.
- LLM returns unknown chunk ids → ignored.
- LLM call raises/times out → fall back to pre-rerank ordering.
- Candidate pool exceeds one LLM context window → must batch, not truncate silently.
- `reranker=None` (default) → output byte-identical to current `retrieve()`.
