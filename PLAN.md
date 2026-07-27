## Solution plan

**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation. https://github.com/ascherj/pathreview/issues/34

### Understand

`HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` ranks chunks by blending
normalized vector-similarity and BM25 keyword scores (`rag/retriever/hybrid.py:78-81`):

```python
blended_score = (
    self.vector_weight * vector_score +
    self.keyword_weight * keyword_score
)
```

Both signals are proxies for relevance (shared vocabulary, or embedding-space
proximity) rather than a judgment of whether the chunk actually answers the query.
Nothing in `retrieve()` checks that. `tests/unit/test_hybrid_retriever.py`
(commit `e97eb8f`) reproduces this: a chunk about "managed weekend shift schedule
at campus bakery" outranks a chunk about "led a team of 4 engineers" for a query
on "leadership and team management experience," because the decoy scores higher
on both blended signals despite being the wrong answer.

**Expected behavior:** the top-k chunks passed to generation should be chunks that
actually address the query, not just chunks that share its vocabulary or sit near
it in embedding space.

**Actual behavior:** `retrieve()` returns whatever ranks highest by blended score
(`hybrid.py:93-97`), with no semantic check in between scoring and return.

### Map

Files expected to touch:

- `rag/retriever/hybrid.py`. No logic change expected inside `retrieve()` itself;
  this is the integration point where a reranking pass gets inserted between the
  blended-score sort (line 94) and the `final_results = results[:max_chunks]`
  slice (line 97).
- `rag/retriever/reranker.py` (new). LLM-based reranker. Takes the top-k blended
  results from `retrieve()` and the original query, scores each chunk's relevance
  with a smaller/cheaper LLM call, and returns a reordered (and/or refiltered)
  list.
- `tests/unit/test_reranker.py` (new). Unit tests for the reranker in isolation
  (mocked LLM client), following the `@pytest.mark.unit` / fixture conventions
  used in `tests/unit/test_relevance_scorer.py` and
  `tests/unit/test_hybrid_retriever.py`.
- `tests/unit/test_hybrid_retriever.py`. Extend once reranking is wired in, to
  confirm the decoy outranks genuine case from the reproduction commit is fixed.

Not touching (explicitly out of scope, see Risks):

- `core/services/review_service.py`. The RAG pipeline entry point
  (`_run_rag_retrieval_generation`, lines 307 to 354) is a stub that never calls
  `HybridRetriever` today, so there's no live caller to update.
- `rag/evaluator/relevance_scorer.py`. A separate, keyword overlap based scorer
  used only by `EvalSuite` for offline evaluation metrics. Unrelated to live
  reranking despite the similar name; not being reused or modified.

### Plan

1. Design the reranker's interface: a `Reranker` (or similarly named) class with a
   `rerank(query: str, chunks: list[dict], top_k: int) -> list[dict]` method,
   mirroring the dict shape `HybridRetriever.retrieve()` already returns
   (`id`, `text`, `metadata`, `score`, ...).
2. Implement the LLM scoring call in `reranker.py`: prompt a smaller/cheaper model
   to output a relevance score (0-1) per chunk given the query, following the
   existing prompt/client patterns in `rag/generator/review_generator.py`
   (`openai.OpenAI` client, `ReviewConfig`-style config).
3. Merge/replace the blended score with the LLM relevance score (decide: fully
   replace, or blend as a third signal alongside vector/keyword) and re-sort.
4. Wire `HybridRetriever` to optionally call the reranker after line 94 in
   `hybrid.py`, gated behind a constructor flag/param so reranking stays opt-in
   (matches the issue's "optional re-ranking pass" framing).
5. Extend `tests/unit/test_hybrid_retriever.py` with the reranker enabled, and add
   `tests/unit/test_reranker.py`, to confirm the decoy case from the reproduction
   commit gets correctly demoted.

### Inputs & outputs

**Input:** the original query string, and the top-k chunk dicts already produced
by `HybridRetriever.retrieve()`'s blended scoring (each with `id`, `text`,
`metadata`, `score`).

**Output:** the same list of chunk dicts, re-ordered (and optionally re-filtered)
by LLM-judged relevance, with the poor semantic matches demoted or dropped before
the list reaches `ReviewGenerator.generate_full_review()`.

### Risks & unknowns

- **Unwired pipeline:** `core/services/review_service.py:307-354` never calls
  `HybridRetriever`. The reranker will be correct but unused by the live app
  until that stub is built out (separate, out of scope issue). Flagging so
  reviewers don't expect an end-to-end demo.
- **Cost/latency:** an LLM call per chunk (or per batch) adds latency and API
  cost to every retrieval. Need to decide batch-scoring vs per-chunk scoring, and
  whether that trade-off is acceptable for `max_chunks` up to 10 (`hybrid.py:29`
  default).
- **No LLM client config confirmed yet:** need to check whether `ReviewConfig`
  (`rag/generator/review_generator.py:14-21`) can be reused for the reranker's
  LLM client, or if a separate lighter-weight config is needed.
- **Score scale mismatch:** blended scores from `retrieve()` are normalized 0-1
  relative to the current candidate set (`hybrid.py:58-59`); LLM relevance scores
  need a comparable scale, or a decision to fully replace rather than blend.

### Edge cases

- Empty chunk list passed to reranker (no candidates from `retrieve()`).
- LLM call fails or times out mid batch. Should degrade gracefully (e.g. fall
  back to original blended ranking) rather than losing all results.
- All chunks score equally low from the LLM (no chunk actually answers the
  query). Need a policy for what gets returned (empty list vs. best available).
- Very long chunk text exceeding the reranker LLM's context/token limits.
- Duplicate or near-duplicate chunks in the top-k (e.g. overlapping text spans)
  scored inconsistently by the LLM across calls.
