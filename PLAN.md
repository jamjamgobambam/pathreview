# Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula —
https://github.com/ascherj/pathreview/issues/36

### Understand

**Root cause.** `docs/ARCHITECTURE.md` describes the RAG system in one sentence
("Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context...",
line 60) but never documents *how* the two scores are combined. The scoring logic
exists and is stable in `rag/retriever/hybrid.py` (`HybridRetriever.retrieve()`,
lines 58–97); it is simply undocumented.

**Expected vs. actual.**
- *Expected:* a reader of ARCHITECTURE.md can understand the blending formula, the
  default weights, how each score is normalized, and can follow a worked example.
- *Actual:* none of that is present; the only way to learn the formula is to read the
  source. This is a Tier 1 "good first issue" docs gap, not a behavioral bug.

The formula, confirmed from source:
`blended = vector_weight · (vec_sim / max_vec) + keyword_weight · (bm25 / max_bm25)`
with defaults `vector_weight = 0.7`, `keyword_weight = 0.3`
(hybrid.py:14), max-normalization per query (hybrid.py:58–59, 70, 76), a `min_score`
filter default `0.3`, and top-`max_chunks` (default 10) returned (hybrid.py:29, 93–97).
Vector similarity itself is `1 / (1 + distance)` (vector_store.py:103).

### Map

Files/functions involved:

| File | Why it matters | Will I edit it? |
|---|---|---|
| `docs/ARCHITECTURE.md` | Where the new section goes (under the RAG System subsection, after line 60) | **Yes — the fix** |
| `rag/retriever/hybrid.py` | Source of truth for weights, normalization, blend, filter (lines 13–97) | No — read only |
| `rag/retriever/vector_store.py` | Distance→similarity conversion (line 103), cosine space (line 36) | No — read only |
| `rag/retriever/keyword_search.py` | Raw BM25 scores (lines 44–59) | No — read only |
| `JOURNAL.md` | Week 8 log entry | Yes — journaling only |

Expected files touched by the actual fix: **`docs/ARCHITECTURE.md` only.**

### Plan

1. **Add a `#### Hybrid Retrieval Scoring` subsection** to `docs/ARCHITECTURE.md`,
   immediately after the RAG System paragraph (line 60), before the Safety Layer heading.
2. **Write the plain-language walkthrough + formula block**, citing the default weights
   (0.7 / 0.3) and the max-normalization of both vector similarity and BM25 scores.
3. **Add the validated numerical example** (candidate table → normalized scores → blended
   scores → `min_score` filter → final ranking) that I reproduced in Week 8.
4. **Add a short "Notes & edge cases" list** (relative per-query normalization, how
   `min_score` interacts with the weights, union semantics for one-sided matches,
   unvalidated weights).
5. **Verify docs render** and run `make check` (docs-only change, but confirm nothing
   breaks), then open a PR against upstream `main` per CONTRIBUTING.md.

### Inputs & outputs

- **Input:** the existing scoring behavior in `rag/retriever/*` (no code changes).
- **Output:** a new prose section in `docs/ARCHITECTURE.md` — formula, default-weights
  table, normalization explanation, one worked numerical example, and an edge-case list.
  No behavioral change to the application.

### Risks & unknowns

- **Docs drifting from code.** If the weights or `min_score` defaults change later, the
  doc goes stale. Mitigation: cite the exact file/line and function so future readers can
  re-verify; keep numbers tied to the documented defaults.
- **Scope creep.** Two real code smells sit next to this logic — (a) `retrieve()` fetches
  `all_chunks` (hybrid.py:50) but never re-indexes the keyword searcher, so the keyword arm
  can be empty; (b) the "euclidean" comment (vector_store.py:102) contradicts the cosine
  space config (vector_store.py:36). These are *not* part of a docs issue. I will document
  intended behavior and flag them in the PR, but not fix code here.
- **Placement/style unknown.** Whether maintainers prefer an inline subsection vs. a new
  ADR for the 0.7/0.3 choice. Default: inline subsection now; offer an ADR follow-up.

### Edge cases

The documentation should explain how the code already handles these, so readers aren't
surprised:

- A chunk found by only one method (vector-only or keyword-only) → the missing side scores
  0.0 (hybrid.py:66–67).
- Empty result sets / all-zero scores → `max(..., default=1.0)` and `> 0` guards prevent
  division by zero (hybrid.py:58–59, 70, 76).
- The `min_score` interaction: with default weights a keyword-only chunk maxes at
  `0.3 × 1.0 = 0.3` (only the top keyword hit can clear the threshold); a vector-only chunk
  needs normalized vector ≥ `0.3 / 0.7 ≈ 0.43`.
- Weights that don't sum to 1 (constructor does not validate) shift the score range.
