## Solution plan

**Issue:** 
Issue #34, https://github.com/ascherj/pathreview/issues/34

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
There is no re-ranker after retrieving the chunks. The optimal pipeline should include a re-ranking step.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
rag/retriever/hybrid.py: contains the retriever
rag/retriever/reranker.py: the new file I created to implement re-ranking.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Widen the candidate pool before truncation.** `HybridRetriever.retrieve()` currently
   blends vector + keyword scores and truncates straight to `max_chunks` (`hybrid.py:111-115`).
   Re-ranking needs a bigger pool to work with than the final answer size, or it can only
   reorder chunks that were already going to be returned. Add a `candidate_multiplier`
   (e.g. fetch/keep `max_chunks * 3` after blending) and pass that pool to the reranker
   before the final cut to `max_chunks`.
2. **Implement `Reranker` in `rag/retriever/reranker.py`.** Takes `(query, candidate_chunks)`,
   builds a single prompt listing each candidate (id + text, truncated to a token budget),
   and asks the LLM to return a relevance score (or rank order) per chunk id as JSON.
   Reuse the OpenAI-client pattern already used in `rag/generator/review_generator.py`
   (`ReviewConfig`, `openai.OpenAI(...)`) instead of inventing a new one.
3. **Parse the LLM output into per-chunk scores.** Mirror `rag/generator/output_parser.py`'s
   approach: parse expected JSON, and if parsing fails or a candidate id is missing from the
   response, fall back to that chunk's existing blended `score` rather than dropping it.
4. **Wire `Reranker` into `HybridRetriever.retrieve()`** (or as an explicit step the caller
   invokes after `retrieve()` — TBD in review) so re-ranking happens on the widened pool,
   then truncate to `max_chunks` only after re-ranking, not before.
5. **Add unit tests with a mocked LLM client** (no real API calls in CI): confirm the
   reranker can invert the ordering demonstrated in
   `tests/unit/test_hybrid_keyword_bias.py` — i.e. that "relevant" outranks "stuffed"
   once re-ranking is applied, closing the loop on the showcased bug.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** the original `query` string, plus the widened candidate pool from
  `HybridRetriever` — each a dict with `id`, `text`, `metadata`, `score`, `vector_score`,
  `keyword_score` (same shape `retrieve()` already returns).
- **Output:** the same list of chunk dicts, reordered by relevance, with an added
  `rerank_score` field (kept separate from the original `score` so the blended score
  stays inspectable/debuggable), truncated to `max_chunks`. No change to the shape
  consumers (`ReviewGenerator.generate_section`) expect — they already just read
  `chunk["text"]`, `chunk["metadata"]`, `chunk["score"]`.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **Cost/latency:** an extra LLM call per retrieval (potentially per section, per review)
  multiplies cost and adds latency to every review — need to confirm whether this is
  one re-rank call per `retrieve()` invocation or something batched/cached across sections.
- **Garbage in, garbage out:** if the true best chunk was never in vector/keyword's
  top-N to begin with (dropped before blending), re-ranking can't recover it — the
  candidate pool widening in step 1 only helps up to how many are fetched from
  `vector_store.query`/`keyword_searcher.search` in the first place.
- **Non-determinism:** LLM-based scoring can be inconsistent run-to-run; need low
  temperature and/or structured output (JSON mode) to keep it stable enough for tests
  and reproducible reviews.
- **Testing without hitting the real API:** need a mock/fake LLM client in unit tests
  (same concern `ReviewGenerator` already has) — haven't decided the mocking pattern yet.
- **Failure handling:** what happens if the LLM call errors, times out, or returns
  malformed output — unsure yet whether to fall back silently to blended-score order
  or surface a warning/log.

### Edge cases
What inputs or states should your fix handle gracefully?

- Empty candidate list (nothing retrieved) — reranker should no-op, not call the LLM.
- LLM response missing scores for some candidate ids — fall back to that chunk's
  existing blended `score` instead of dropping the chunk.
- LLM call fails or times out — fall back to the existing blended-score ordering
  (i.e. re-ranking failure should degrade to current behavior, not break retrieval).
- Candidate pool larger than the LLM's context/token budget — cap how many chunks
  are sent to the reranker (e.g. top N by blended score) rather than truncating text
  mid-chunk unpredictably.
- Tied rerank scores — stable sort falling back to original blended score as tiebreaker.