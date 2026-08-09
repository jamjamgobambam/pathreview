## Solution plan

**Issue:** #24 — Hybrid retriever over-weights keyword results when query contains technology names
https://github.com/ascherj/pathreview/issues/24

### Understand
`HybridRetriever.retrieve()` blends vector similarity and BM25 keyword scores with a fixed
0.7/0.3 weighted sum (`rag/retriever/hybrid.py:78-81`). Before blending, each score is
normalized by dividing by the **max raw score in the current result batch**
(`hybrid.py:58-59, 70, 76`).

BM25 raw scores are unbounded and grow with term repetition within a chunk. A chunk that
repeats query terms many times (e.g. a README listing "Python React Python React..." several
times) produces an outlier raw BM25 score. Because normalization divides by the batch's own
max, that outlier becomes the denominator — guaranteeing the stuffed chunk a normalized
keyword_score of 1.0, regardless of whether it's actually relevant. A genuinely relevant chunk
that mentions each term once gets a much smaller keyword_score by comparison, even when it has
the strongest vector similarity in the batch.

A secondary, compounding bug: `KeywordSearcher._tokenize()` only lowercases and splits on
whitespace (`keyword_search.py:76`), so a term followed by punctuation (e.g. "React.",
"Python,") doesn't match the query token ("react", "python"). This further suppresses BM25
scores for legitimately relevant chunks whose sentences end mid-term.

**Expected:** a chunk that is genuinely relevant to the query semantically should outrank a
chunk that merely repeats the query's vocabulary many times without being topically relevant.

**Actual:** confirmed via `tests/unit/test_hybrid_retriever.py` (currently marked
`xfail(strict=True)`) — the keyword-stuffed, irrelevant `readme_1` chunk outranks the genuinely
relevant `resume_1` chunk at the default 0.7/0.3 weight split.

**Root cause:** per-batch max-score normalization in `hybrid.py` lets a single outlier BM25
score set the scale for the whole batch, combined with a naive tokenizer that produces false
negatives on punctuation-adjacent terms.

I considered (and ruled out) a fix based on cross-document term frequency — i.e. downweighting
a query term if it appears in most of a profile's own chunks. I verified numerically that this
would not have fixed the reproduction case: "python"/"react" only appear as exact tokens in 1
of the 4 test chunks, so a cross-chunk-commonality check reports them as rare/discriminative,
not common. The actual defect is repetition *within a single chunk*, which is a different
statistic. This ruled out that approach before it was implemented.

### Map
- `rag/retriever/hybrid.py` — `retrieve()` (lines ~44-104). Primary change: replace the
  per-batch max-score normalization/linear blend with weighted Reciprocal Rank Fusion (RRF).
- `rag/retriever/keyword_search.py` — `_tokenize()` (lines 66-76). Secondary fix: strip
  punctuation so terms like "Python," and "React." match query tokens.
- `tests/unit/test_hybrid_retriever.py` — remove the `xfail` marker (lines 54-58) once the fix
  makes the test pass; this becomes the permanent regression test.
- `tests/unit/test_keyword_search.py` — existing tests to re-check against the tokenizer
  change, especially `test_special_characters_in_query` (line 193, tests `"c++"` — must confirm
  punctuation-stripping doesn't silently break special-character tokens).

### Plan
1. Add a `_rank_map(results, score_key)` helper (or inline equivalent) in `hybrid.py` that
   converts a list of scored results into `{chunk_id: rank}`, rank 1 = highest score, with
   deterministic tie-breaking (stable sort on original order, matching current behavior).
2. Replace the normalize-by-batch-max blend (`hybrid.py:58-90`) with weighted RRF:
   `blended_score = vector_weight / (k + vector_rank) + keyword_weight / (k + keyword_rank)`,
   using a `k` constant sized for small per-profile result sets (start at `k=10`, not the
   standard large-corpus `k=60` — see Risks). Chunks missing from one side's results get that
   side's rank treated as "beyond max" (e.g. `len(all_ids) + 1`) rather than a score of 0.
3. Fix `KeywordSearcher._tokenize()` to strip leading/trailing punctuation per token while
   preserving internal characters (so "c++", "node.js" style tokens aren't mangled) — verify
   against `test_special_characters_in_query`.
4. Remove the `xfail` marker from `test_relevant_chunk_outranks_keyword_stuffed_irrelevant_chunk`
   and confirm it passes; run the full `test_hybrid_retriever.py` and `test_keyword_search.py`
   suites to confirm no regressions.
5. Add 1-2 new unit tests: a case where keyword matching *should* win (e.g. an exact rare
   identifier/acronym match with weak vector similarity) to confirm RRF didn't overcorrect
   toward vector-only ranking.

### Inputs & outputs
- **Input:** a text `query`, its embedding, and the profile's chunk corpus (unchanged
  `retrieve()` signature — `query`, `profile_id`, `query_embedding`, `max_chunks`, `min_score`).
- **Output:** same shape as today (`list[dict]` with `id`, `text`, `metadata`, `score`,
  `vector_score`, `keyword_score`), but `score` is now an RRF value in a much smaller numeric
  range than the current 0-1 blend. `vector_score`/`keyword_score` in the output should likely
  become rank-derived values (e.g. `1/(k+rank)`) rather than the old normalized 0-1 scores, so
  callers relying on those fields see consistent semantics — needs confirming no other code
  depends on their current 0-1 scale (checked: nothing outside `hybrid.py`'s own tests
  currently consumes `HybridRetriever`, so this is currently a contained change).
- **Change in behavior:** ranking order for queries containing repeated/common terms; overall
  score magnitudes for all queries (smaller, non-percentage numbers) — `min_score` default of
  `0.3` in `retrieve()` will no longer make sense against RRF's small values and needs revisiting.

### Risks & unknowns
- **`min_score` default (`0.3`) is calibrated for the old 0-1 blended scale.** Under RRF, scores
  are on the order of `0.01-0.1` (see prototype numbers below), so `min_score=0.3` would filter
  out *everything*. This default must change, or `min_score` semantics must change (e.g. become
  a percentile/rank cutoff instead of an absolute score threshold).
- **RRF's `k` constant needs empirical tuning.** I validated the fix works at `k=60, 20, 10, 5`
  on the reproduction case, with `resume_1` beating `readme_1` at every value tested, but the
  margin is thin at `k=60` (0.016237 vs 0.016208) and much clearer at `k=10` (0.086713 vs
  0.085606). No corpus-size-aware guidance exists yet for picking `k` in this codebase — I'm
  starting from `k=10` but this should be validated against `rag/evaluator/relevance_scorer.py`
  or real profile data, not just the one hand-built test case.
  <!-- resume_1=0.7/(k+1)+0.3/(k+3), readme_1=0.7/(k+2)+0.3/(k+1); verified via a standalone
  Python calculation before writing this plan (not part of the repo, not committed). -->
- **RRF discards score magnitude.** A chunk that barely edges out another in vector similarity
  is ranked the same (rank 2) as one that's a distant runner-up. This trades away information
  the current linear blend has; unclear if any downstream consumer (once `HybridRetriever` is
  actually wired into the pipeline — currently nothing calls it outside tests) will care about
  score magnitude rather than just rank order.
  <!-- Verified via `grep -rln "HybridRetriever\|KeywordSearcher"`: only the two test files
  reference these classes today. -->
- **Tokenizer change could regress special-character handling.** Naive punctuation-stripping
  risks breaking tokens like "c++" or "node.js" into "c", "node", "js". Needs a punctuation
  regex that's deliberately conservative (strip only leading/trailing punctuation, not
  mid-token), and `test_special_characters_in_query` needs to keep passing.
- **`retrieve()` never calls `keyword_searcher.index()` itself** — noted in the existing test
  file's docstring as "a separate gap from issue #24." Not in scope for this fix, but worth
  flagging since it means `HybridRetriever` isn't fully wired into a real pipeline yet; this fix
  is validated against the unit test's hand-built scenario, not a live end-to-end run.

### Edge cases
- Empty result sets from either vector or keyword search (already handled today via
  `default=1.0` on the max calculations — needs an equivalent for rank-based lookup, e.g. a
  chunk absent from keyword results gets the worst possible keyword rank, not an undefined one).
- A query with no keyword overlap at all (all BM25 scores 0, e.g. `test_query_matching_no_documents`)
  — ranks must still be well-defined (ties broken deterministically) so RRF doesn't crash on
  degenerate/all-zero score arrays.
- A single-chunk corpus — rank is always 1 for every chunk; RRF should reduce gracefully to
  weighting by presence, not error out on divide-by-zero or similar.
- Query containing only stopword-like tokens with no matches in either search method.
- Ties in vector or keyword score across multiple chunks (current stable-sort tie-breaking by
  original order should be preserved so behavior stays deterministic for tests).
