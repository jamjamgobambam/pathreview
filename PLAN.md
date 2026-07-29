# Solution plan

**Issue:** [Implement a re-ranking step that uses an LLM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

### Understand

**Root cause / gap.** The retrieval pipeline has no relevance re-ranking. In
[`rag/retriever/hybrid.py`](rag/retriever/hybrid.py#L92-L104), `HybridRetriever.retrieve()`
blends a vector-similarity score and a BM25 keyword score into a single
`blended_score`, sorts candidates by it, and returns the top `max_chunks`.
That blended score is a lexical/embedding proxy for relevance — it does not
model whether a chunk actually answers the *specific* query. So the top-k
chunks that get passed to the generator
([`rag/generator/review_generator.py`](rag/generator/review_generator.py#L39-L74))
can be sub-optimal.

**Expected vs. actual.**
- *Actual:* chunks are ordered only by `vector_weight * vector_score + keyword_weight * keyword_score`. No LLM judges relevance.
- *Expected:* when re-ranking is **enabled**, an LLM scores each candidate chunk for relevance to the query and the candidates are reordered by that score before top-k selection. When re-ranking is **disabled** (default), behavior is byte-for-byte identical to today.

### Map

Files I expect to touch:

- **`rag/retriever/reranker.py`** *(new)* — `LLMReranker` class: `rerank(query, chunks, top_k)` plus a private `_score_chunk(query, chunk)` that calls the LLM and parses a relevance score. Owns the prompt, parsing, and fallback logic.
- **`rag/retriever/hybrid.py`** — add an optional `reranker` dependency and a `rerank: bool = False` flag (or `enable_rerank`) to `retrieve()`. When on, retrieve a wider candidate pool, rerank, then take top-k. When off, unchanged.
- **`core/config.py`** — add settings: `enable_reranking: bool = False`, `rerank_model: str`, `rerank_candidate_multiplier: int` (how many candidates to over-fetch before reranking). Keeps the feature opt-in via env var.
- **`tests/unit/test_reranker.py`** *(new, Week 9)* — unit tests for `LLMReranker` using mocked LLM responses: reorder-by-score, top_k limit, empty input, and LLM-failure fallback.
- **`tests/unit/test_hybrid_retriever.py`** *(new, if not present)* — assert disabled path is unchanged and enabled path reorders.

Reference-only (to mirror existing patterns, not change):
- [`rag/generator/review_generator.py`](rag/generator/review_generator.py#L34-L37) — how the `openai.OpenAI(base_url=...)` client is constructed and called; the reranker should reuse the same client style.
- [`rag/generator/output_parser.py`](rag/generator/output_parser.py) — parsing LLM text output robustly.

### Plan

1. **Build `LLMReranker`.** Implement `rerank()` and `_score_chunk()` in `rag/retriever/reranker.py`. `_score_chunk` sends the query + chunk text to the LLM asking for a 0–1 relevance score, parses the number, and defaults safely on parse failure. `rerank()` scores each candidate, sorts descending, returns top-k. On any LLM exception, log and return the input order truncated to top-k (graceful fallback).
2. **Wire into `HybridRetriever`.** Accept an optional `reranker` in `__init__` and a `rerank` flag in `retrieve()`. When enabled, over-fetch candidates (e.g. `max_chunks * multiplier`) before reranking so the LLM has a real pool to reorder.
3. **Add config + defaults.** Add the settings in `core/config.py`, defaulting the feature OFF so existing behavior is preserved with zero config change.
4. **Add unit tests with mocked LLM responses.** Cover reorder-by-score, top_k limit, empty input, and LLM-failure fallback — no live API calls in tests.
5. **Add hybrid integration tests + docs.** Test the enabled/disabled paths in `HybridRetriever`, and add a short note to the README/docs describing the flag.

### Inputs & outputs

- **Input:** a text `query` (str) and a list of candidate chunk dicts (each with `id`, `text`, `metadata`, `score`) as produced by `HybridRetriever`, plus `top_k` (int).
- **Output:** a list of the same chunk dicts, length ≤ `top_k`, reordered by LLM relevance. (Stretch: attach a `rerank_score` field for observability, without removing the existing `score`.)
- **Side effects:** LLM API calls (one per candidate, or one batched call) via the configured OpenRouter/OpenAI client; structured log lines mirroring the existing `logger.info(...)` style in `hybrid.py`.

### Risks & unknowns

- **Latency & cost.** One LLM call per chunk multiplies calls per query. Mitigation: only rerank a bounded candidate pool, consider a single batched prompt scoring all chunks at once. Unknown: how the free `google/gemma-3-27b-it:free` model in `core/config.py` handles a batched scoring prompt.
- **Score parsing fragility.** The LLM may return prose instead of a bare number. Mitigation: strict prompt + regex extraction + default score on failure (mirror `output_parser.py`'s defensive parsing).
- **Preserving disabled behavior.** The grading emphasis is that disabling rerank keeps existing behavior identical. Risk: accidentally changing the candidate count or sort. Mitigation: guard all new logic behind the flag and keep a regression test asserting the disabled path.
- **Test env has no live LLM.** `llm_provider` defaults to `mock` and there may be no API key. Mitigation: all tests mock the client; never hit the network.
- **Where to inject the client.** Unknown whether to construct the OpenAI client inside `LLMReranker` or inject it. Leaning toward injection (like the test fixtures) for testability, matching `ReviewGenerator`'s config-driven construction.

### Edge cases

- **Empty candidate list** → return `[]`, make zero LLM calls.
- **Fewer candidates than `top_k`** → return all, no padding.
- **LLM call raises / times out** → fall back to the incoming hybrid order, truncated to `top_k`; never drop the pipeline.
- **LLM returns unparseable or out-of-range score** → clamp to `[0, 1]` / assign a default, don't crash.
- **Ties in relevance score** → stable order (fall back to original hybrid position) so results are deterministic.
- **Reranking disabled** → `retrieve()` output is identical to current behavior (same chunks, same order).
- **Chunk with empty `text`** → scored as minimally relevant rather than erroring.
