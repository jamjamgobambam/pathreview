# Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula — https://github.com/ascherj/pathreview/issues/36

### Understand

**Root cause.** `docs/ARCHITECTURE.md` mentions hybrid retrieval in exactly one
sentence (the RAG System subsystem, currently line 60):

> Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context…

It names the two signals but never explains how they are combined into the single
score used for ranking. A reader cannot answer any of: *How are the two scores
blended? Are they normalized first? What are the default weights? What score is
required to survive the cutoff?* All of that logic lives in
[`rag/retriever/hybrid.py`](rag/retriever/hybrid.py) but is undocumented.

**Expected vs. actual.**
- *Expected:* the architecture doc explains the blending formula, the
  normalization step, the default weights, and the `min_score` cutoff, with a
  worked example.
- *Actual:* the doc only states that a blend happens.

This is a documentation gap, not a code bug — no runtime behavior changes.

### Map

Files involved:

| File | Role in the fix |
|---|---|
| `docs/ARCHITECTURE.md` | **Edited** — add the scoring-formula section (the only file the fix touches). |
| `rag/retriever/hybrid.py` | Read-only — source of truth for the blend formula, weights, and `min_score`. |
| `rag/retriever/vector_store.py` | Read-only — defines the vector `score` as `1 / (1 + distance)` (higher = better). |
| `rag/retriever/keyword_search.py` | Read-only — defines the BM25 `bm25_score` and whitespace/lowercase tokenization. |

Only `docs/ARCHITECTURE.md` is modified.

### Plan

1. **Add a "Hybrid Retrieval Scoring" subsection** under RAG System (`rag/`) in
   `docs/ARCHITECTURE.md`, right after the existing one-sentence description.
2. **Document the pipeline** end to end: vector search (`1/(1+distance)`
   similarity) and BM25 keyword search each fetch `max_chunks * 2` candidates,
   scores are normalized, blended, filtered, and the top `max_chunks` returned.
3. **State the formula and defaults** explicitly:
   `blended = vector_weight * vector_score + keyword_weight * keyword_score`,
   with defaults `vector_weight = 0.7`, `keyword_weight = 0.3`, and
   `min_score = 0.3`. Note that a chunk found by only one retriever contributes
   `0` for the missing signal.
4. **Describe the normalization accurately.** The code divides each score by the
   **max** score in its own result set (max-normalization to 0–1), *not* the
   min-max normalization the issue text describes. Document what the code
   actually does. (See Risks — I'll confirm the intended wording with the
   maintainer.)
5. **Add a worked example** with concrete numbers so the formula is illustrated,
   then wire the new section into the doc (heading level + any ToC/links).

### Inputs & outputs

- **Input:** the retrieval logic in `rag/retriever/hybrid.py` (and the score
  definitions in `vector_store.py` / `keyword_search.py`).
- **Output:** a new prose + example section in `docs/ARCHITECTURE.md`. No code,
  tests, or migrations change; the app builds and runs identically.

### Worked example (draft, to refine in the doc)

Query returns chunk A (vector only), chunk B (both), chunk C (keyword only).

| Chunk | raw vector | raw bm25 | vec_norm | key_norm | blended (0.7/0.3) | kept (≥0.3)? |
|---|---|---|---|---|---|---|
| A | 0.80 | — | 0.80/0.80 = 1.00 | 0.00 | 0.70 | yes |
| B | 0.60 | 4.0 | 0.60/0.80 = 0.75 | 4.0/5.0 = 0.80 | 0.765 | yes |
| C | — | 5.0 | 0.00 | 5.0/5.0 = 1.00 | 0.30 | yes (== cutoff) |

Ranking: B (0.765) > A (0.70) > C (0.30). Numbers to be re-verified against the
code before publishing.

### Risks & unknowns

- **Normalization wording mismatch.** The issue says "min-max normalized"; the
  code uses max-only normalization (`score / max`, no `min` subtracted). I'll
  document the actual behavior and confirm with the maintainer whether the code
  or the description is the intended one — if the code is "wrong," that becomes a
  separate code issue, out of scope here.
- **Score semantics.** Vector `score` is a similarity (`1/(1+distance)`, higher
  better) while BM25 is an unbounded relevance score — worth making explicit so
  readers don't assume both are cosine similarities.
- **Doc drift.** Hard-coded defaults (0.7 / 0.3 / 0.3) in the doc could fall out
  of sync with the code later. Mitigate by pointing to `HybridRetriever` as the
  source of truth rather than implying the doc is authoritative.

### Edge cases (to mention in the doc)

- A chunk retrieved by only one method → the other signal is `0`.
- Empty result set → `max` defaults to `1.0`, avoiding divide-by-zero.
- All blended scores below `min_score` → empty result list is returned.
- Fewer than `max_chunks` survivors → all survivors returned, unpadded.
