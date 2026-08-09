## Solution plan

**Issue:** [
    Hybrid retriever over-weights keyword results when query contains technology names
    #24
    https://github.com/ascherj/pathreview/issues/24
 ]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

**Root cause.** `HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` blends a vector-similarity score and a BM25 keyword score with fixed, equal weights (the issue describes 50/50; the fix moves this toward vector). Both scores are max-normalized to 0–1 independently (`hybrid.py:58-59`) *before* blending. Normalization means a chunk that is merely the *best keyword match in its batch* gets `keyword_score = 1.0` regardless of how weakly it matches in absolute terms. When a query contains a technology name ("React", "Python") that appears in both the resume and the README, a keyword-stuffed but semantically-irrelevant chunk earns a top-normalized BM25 score and, at equal weight, outranks the genuinely relevant chunk.

**Expected:** for a query about the candidate's React experience, the top chunk should be the resume/project chunk that is *semantically* about React work.
**Actual (reproduced in `scripts/repro_issue_24.py`):** at 50/50 the README chunk wins purely on keyword score (`final=0.794` vs `0.667`) despite a weaker vector score, so the wrong document is retrieved and fed to the LLM.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

**Will touch:**
- `rag/retriever/hybrid.py` — `HybridRetriever.__init__` / `retrieve()`. Primary change: source the blend weights from config instead of hardcoded defaults, and add input validation. The blend expression at `hybrid.py:78-81` stays but its weights change.
- `core/config.py` — `Settings` class (alongside `max_chunks_per_query`, `min_relevance_score` at lines 36-37). Add `hybrid_vector_weight` and `hybrid_keyword_weight` fields so the ratio is env-configurable and has one source of truth.
- `scripts/repro_issue_24.py` — extend into / mirror as a real regression test asserting the correct chunk ranks first at the tuned weights.

**Will read / investigate (likely no change):**
- `rag/retriever/keyword_search.py` — `KeywordSearcher.search()` and `_tokenize()`; confirm normalization assumptions and whether naive tokenization worsens the shared-vocabulary problem.
- `rag/retriever/vector_store.py` — `VectorStore.query()`; confirm the `1/(1+distance)` similarity range so weight tuning reasons over comparable scales.
- `rag/generator/review_generator.py` — `_format_context()` / `generate_section()`; the downstream consumer, to sanity-check the end-to-end effect.
- `core/services/review_service.py` — `_run_rag_retrieval_generation()` (still a placeholder); confirms the fix isn't yet on the live path and won't be exercised via the API.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Add config fields.** In `core/config.py`, add `hybrid_vector_weight: float = Field(default=0.8)` and `hybrid_keyword_weight: float = Field(default=0.2)` to `Settings`, next to the existing retrieval knobs. This removes the "no config constant" gap noted in the journal.
2. **Wire weights + validation into the retriever.** In `rag/retriever/hybrid.py`, default the constructor args to the config values (`settings.hybrid_vector_weight` / `settings.hybrid_keyword_weight`) and add a guard in `__init__` that rejects negative weights and normalizes if the two don't sum to 1.0 (so a misconfigured ratio can't silently skew scores).
3. **Add a regression test from the repro.** Promote the scenario in `scripts/repro_issue_24.py` into a `pytest` test (e.g. `tests/test_hybrid_retriever.py`) that builds the two-chunk resume-vs-README fixture, runs `retrieve()`, and asserts the resume chunk ranks #1 at the default (tuned) weights — and still ranks #2 at 50/50, locking in the reproduction.
4. **Verify end-to-end formatting is unaffected.** Confirm `review_generator._format_context()` still receives correctly-ordered chunks and that the `min_score` filter at `hybrid.py:93` behaves sensibly after re-weighting (a lower keyword contribution shouldn't drop everything below threshold).
5. **Update docs.** Record the final chosen ratio and rationale in `JOURNAL.md` (Affected parts already notes 0.8/0.2) and note the new env vars.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

**Inputs:** unchanged `retrieve()` signature — `query: str`, `profile_id: str`, `query_embedding: list[float]`, `max_chunks: int`, `min_score: float` — plus the two new blend-weight settings read from `core/config.py` (overridable via `.env` / environment: `HYBRID_VECTOR_WEIGHT`, `HYBRID_KEYWORD_WEIGHT`).

**Outputs / changes:**
- Same return shape: `list[dict]` with `id`, `text`, `metadata`, `score`, `vector_score`, `keyword_score` — no consumer (`review_generator._format_context`) needs changes.
- Behavioral change: the blended `score` now weights vector similarity more heavily, so ranking order changes for tech-name queries — the relevant-document chunk rises to the top.
- New: a config-driven, validated weight pair (single source of truth) and a regression test asserting the corrected ranking.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **Over-correcting toward vector.** 0.8/0.2 fixes the reproduced case, but I haven't validated against a corpus where BM25 legitimately helps (exact-term queries like a specific library or error string). Risk: recall drops for genuinely keyword-driven queries. Mitigation/investigation: test a small matrix of query types before locking the ratio; consider query-adaptive weighting as a follow-up (already flagged in the journal).
- **Normalization interacts with weights.** The max-normalization at `hybrid.py:58-59` means weights act on *relative* not absolute scores; changing weights doesn't fix the underlying "best-in-batch always gets 1.0" behavior. Unknown: whether re-weighting alone is enough, or whether the normalization scheme itself needs revisiting.
- **`min_score` threshold coupling.** `hybrid.py:93` filters on the blended score, and `core/config.py:37` sets `min_relevance_score=0.3`. Lowering the keyword contribution shifts the blended-score distribution; a chunk formerly above 0.3 might now fall below it. Risk: fewer/no chunks returned in edge configs.
- **Not on the live path.** `core/services/review_service.py` `_run_rag_retrieval_generation()` is a placeholder, so I can't validate through the real API yet — end-to-end confidence relies on the isolated repro/test until that's wired up.
- **Naive tokenization.** `keyword_search._tokenize()` lowercases and splits on whitespace only, so "react," / "React." / "react-dom" tokenize inconsistently — this may amplify or mask the effect and could confound test results.

### Edge cases
What inputs or states should your fix handle gracefully?

- **Weights that don't sum to 1** (e.g. `0.7`/`0.7` from a bad `.env`): validate/normalize in `__init__` rather than silently producing inflated blended scores.
- **A weight of exactly 0** (pure-vector or pure-keyword mode): should be allowed and behave as a clean single-retriever fallback, not divide-by-zero or error.
- **Empty result sets / empty index:** `keyword_searcher.search()` returns `[]` on an unbuilt index (`keyword_search.py:40-42`) and vector results can be empty — the `default=1.0` in the `max(...)` normalization (`hybrid.py:58-59`) must keep protecting against division by zero.
- **Chunk in only one retriever's results:** the union loop at `hybrid.py:63-76` already handles a chunk present in vector-only or keyword-only maps; the fix must preserve that (missing side scored 0.0).
- **All chunks below `min_score` after re-weighting:** decide expected behavior (return empty vs. relax) and cover it, since re-weighting shifts the distribution.
- **Ties / identical blended scores:** ensure sort at `hybrid.py:94` is stable/deterministic so ordering doesn't flap between runs.
- **Query containing the tech name many times** (the core case): confirm a keyword-stuffed wrong-doc chunk no longer reaches #1 — this is exactly the regression test's assertion.
