## Solution plan

**Issue:** [#34 — Implement a re-ranking step that uses an LLM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

### Understand

**Root cause.** `HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` produces its
final ranking from a single mechanical signal: a weighted blend of vector cosine
similarity (`vector_weight`, default 0.7) and normalized BM25 keyword score
(`keyword_weight`, default 0.3). At lines 92–97 it filters by `min_score`, sorts
by that blended score, and slices the top `max_chunks`. Nothing between the sort
and the top-k cut evaluates whether a chunk *actually answers the query* — only
surface-level lexical/embedding overlap.

**Expected vs. actual.**
- *Actual:* ranking = blended vector+BM25 score only. A chunk that is semantically
  the best answer but has modest lexical/embedding overlap can score below the
  `max_chunks` cutoff and never reach the generator.
- *Expected (this fix):* an **optional** second-stage pass re-scores the candidate
  set with a smaller LLM for query relevance and reorders before the top-k cut.
  The toggle is **off by default**, so existing behavior is unchanged unless
  explicitly enabled.

### Map

Files I expect to touch:

| File | Change |
|------|--------|
| `rag/retriever/reranker.py` | **New.** `LLMReranker` class: prompts an LLM to score each candidate chunk's relevance (0–1) to the query and returns reordered chunks. Mirrors the `openai.OpenAI` client + config pattern from `ReviewGenerator`. |
| `rag/retriever/hybrid.py` | **Modify.** Add optional `reranker` + `enable_rerank` params to `__init__`; invoke the reranker in `retrieve()` between the blended sort (line 94) and the top-k slice (line 97), behind the toggle. |
| `tests/unit/test_reranker.py` | **New.** Unit test with the LLM call mocked; asserts the reranker can promote a semantically-better, lower-blend chunk above a higher-blend one, and that `enable_rerank=False` leaves order untouched. |

Reference patterns (read-only, not modified):
- `rag/generator/review_generator.py` — `ReviewConfig` + `openai.OpenAI` client usage.
- `rag/generator/prompt_templates.py` — prompt construction style.
- `rag/evaluator/relevance_scorer.py` — existing (keyword-based) relevance scoring interface.
- `tests/unit/test_keyword_search.py`, `tests/unit/test_relevance_scorer.py` — test conventions.

### Plan

1. **Build `LLMReranker`** in `rag/retriever/reranker.py`: a config dataclass
   (api_key, base_url, model, temperature) and a `rerank(query, chunks, top_k)`
   method that prompts the LLM to return a relevance score per chunk, attaches a
   `rerank_score`, and returns chunks sorted by it. Parse defensively and fall
   back to the original order on any parse/API failure.
2. **Wire the toggle into `HybridRetriever`**: add `reranker=None` and
   `enable_rerank=False` to `__init__`; in `retrieve()`, when enabled, run the
   reranker over the filtered candidate pool (slightly larger than `max_chunks`)
   *before* the final `results[:max_chunks]` slice.
3. **Add the unit test** in `tests/unit/test_reranker.py` with the LLM mocked
   (monkeypatch/`unittest.mock`), covering: rerank reorders as expected, disabled
   toggle is a no-op, and the fallback-on-error path preserves original order.
4. **Verify no regression**: run `make test-unit`; confirm the existing hybrid /
   keyword-search tests still pass with the default (rerank off).
5. **Update JOURNAL.md** and this PLAN.md as understanding evolves in Week 9.

### Inputs & outputs

- **Input:** the query string and the candidate `list[dict]` chunks that
  `retrieve()` has already produced (each with `id`, `text`, `metadata`, `score`,
  `vector_score`, `keyword_score`); plus LLM config (api_key/base_url/model).
- **Output:** the same list of chunk dicts, reordered by LLM relevance and sliced
  to `max_chunks`, each carrying an added `rerank_score` field. When the toggle is
  off, output is byte-for-byte the current behavior.

### Risks & unknowns

- **No API key / cost / latency in dev.** The reranker adds an LLM call per
  retrieval. Mitigation: default off; mock in tests; consider batching all
  candidates into one prompt rather than N calls.
- **LLM output parsing.** The model may return malformed or partial scores.
  Mitigation: defensive parsing in `reranker.py` with fallback to the original
  blended order (never crash `retrieve()`).
- **Config plumbing unknown.** I still need to confirm how `HybridRetriever` is
  constructed at call sites (who would pass the `reranker`) — likely in the
  retrieval/orchestration layer (`agent/orchestrator.py` or a factory). Need to
  trace that before finalizing the `__init__` signature.
- **Chunk-dict shape assumptions.** The reranker must not assume keys beyond what
  `retrieve()` guarantees (`id`, `text`); `text` could be empty for
  keyword-only chunks.

### Edge cases

- Empty candidate set → return `[]` without calling the LLM.
- Fewer candidates than `max_chunks` → rerank all, return all.
- Chunk with empty/missing `text` → skip scoring gracefully, keep at original rank.
- LLM returns fewer/more scores than chunks, or non-numeric scores → fall back to
  blended order for the unscored chunks.
- `enable_rerank=False` or `reranker is None` → exact current behavior (no LLM call).
- Ties in `rerank_score` → stable, deterministic tiebreak on the original blended score.
