## Solution plan

**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation (#34) — https://github.com/ascherj/pathreview/issues/34

### Understand

**Expected behavior:** Before retrieved chunks are handed to the generator, the system should check whether each chunk is actually relevant to the specific query — not just similar by vector/keyword score — and use that to reorder or trim the candidate set.

**Actual behavior:** `HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` only ranks chunks by a weighted blend of vector similarity and BM25 keyword scores. Neither signal evaluates relevance to the specific query text, so a chunk can score well on both and still be off-topic, and there is no step that filters or demotes it before it reaches the generator.

**Root cause:** the feature simply doesn't exist yet — confirmed by `grep -rni "rerank" --include="*.py" .` returning zero matches anywhere in the repo (see `JOURNAL.md` reproduction notes and commit https://github.com/adumasiv/pathreview/commit/82afc3cfa309b1e70ef70dbdab46d9567c20cf99). This isn't a logic bug in existing code; it's a missing pipeline stage.

### Map

- `rag/retriever/hybrid.py` — `HybridRetriever.__init__` and `HybridRetriever.retrieve()`; this is where the blended candidate list is produced, sorted, and truncated to `max_chunks`. The rerank step needs to slot in after the blend/filter and before the final truncation.
- `rag/retriever/reranker.py` *(new)* — houses the re-ranking abstraction itself (`Reranker` ABC, an `LLMReranker` that calls a small model, and a `MockReranker` for tests), following the existing `EmbeddingProvider`/`Mock*`/`get_*_provider()` pattern in `ingestion/embeddings/provider.py`.
- `rag/generator/review_generator.py` — not modified, but its `openai.OpenAI(api_key=..., base_url=...)` client pattern is the template for how `LLMReranker` talks to OpenAI/OpenRouter.
- `core/config.py` — needs new settings (`reranker_enabled`, `reranker_model`, `rerank_candidates`) so the reranker can be toggled/configured per environment, consistent with existing `llm_provider`/`openrouter_model` fields.
- `tests/unit/test_reranker.py` *(new)* and `tests/unit/test_hybrid_retriever.py` *(new)* — unit coverage for the new module and its wiring into the retriever.
- Not touched: `core/services/review_service.py` — its RAG step is still a placeholder/stub unrelated to this issue, so full end-to-end wiring is out of scope here.

### Plan

1. Build `rag/retriever/reranker.py`: `Reranker` ABC, `LLMReranker` (prompts a small model for a 0.0–1.0 relevance score per chunk, with defensive parsing and a safe fallback on error), `MockReranker` (deterministic keyword-overlap scoring for tests), and a `get_reranker(provider_name, **kwargs)` factory.
2. Extend `HybridRetriever.__init__` with optional `reranker` and `rerank_candidates` params, defaulting to `None`/off so existing behavior is unchanged when unset.
3. In `HybridRetriever.retrieve()`, after the existing blend/filter/sort step, if a reranker is configured and results are non-empty, slice the top `rerank_candidates`, call `reranker.rerank(query, candidates)`, and use that order for the final `max_chunks` truncation.
4. Add `reranker_enabled`, `reranker_model`, `rerank_candidates` to `core/config.py`.
5. Write unit tests: `MockReranker`/`LLMReranker` scoring and ordering (including malformed-response and API-error fallback), `get_reranker` factory validation, and `HybridRetriever` behavior with/without a reranker attached. Run `make check && make test-unit` and confirm no regressions vs. the pre-change baseline.

### Inputs & outputs

**Input:** the original query string, plus the current candidate chunk list (each a dict with `id`, `text`, `metadata`, and the existing blended `score`) that `HybridRetriever.retrieve()` has already produced.

**Output:** the same chunk list, re-ordered by a new `rerank_score` field (0.0–1.0) added to each chunk dict, then truncated to `max_chunks` — the shape of each returned chunk is unchanged, only its score/order.

### Risks & unknowns

- **Latency/cost:** re-ranking calls the LLM once per candidate (up to `rerank_candidates`, default 25), which could be slow or hit rate limits on a free-tier OpenRouter model. Mitigated by making it opt-in via `reranker_enabled`; batching into a single multi-chunk prompt is a possible follow-up if this proves to be a real problem.
- **Score parsing brittleness:** small/free LLMs don't always return a bare number. The parser extracts the first number via regex and clamps to `[0, 1]`, falling back to `0.0` on any parse or API failure so one bad response can't crash retrieval — but a chunk could be silently under-scored if the model's response is malformed. This is logged via `structlog` so it's observable.
- **No live integration test:** all planned unit tests use `MockReranker` or a mocked OpenAI client; there's no test against a real OpenRouter endpoint, so real-world prompt/scoring quality is unverified until manually tried.
- **Unknown:** exact prompt wording/temperature that gets reliable numeric scores out of the configured free model (`google/gemma-3-27b-it:free`) hasn't been validated against live traffic yet — may need iteration after a manual smoke test.

### Edge cases

- Empty candidate list (e.g., `min_score` filters everything out) — reranker must not be called at all, not just handle an empty list.
- Reranker configured but chunk `text` is empty/whitespace-only — should score low, not error.
- LLM API call throws (timeout, auth failure, rate limit) — must fall back to a defined score (0.0) rather than raising and breaking retrieval.
- LLM response isn't a clean number (e.g., "I'd say around 0.8" or empty string) — regex-based parser must extract or safely default without crashing.
- `rerank_candidates` larger than the number of available results — should just rerank everything available, no index errors.
- Reranker returns scores that tie — sort must remain stable/deterministic enough for tests to assert on order.
