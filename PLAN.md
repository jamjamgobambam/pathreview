## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula #36](https://github.com/ascherj/pathreview/issues/36)

### Understand

`docs/ARCHITECTURE.md` describes the RAG system as using "Hybrid retrieval
(vector similarity + BM25 keyword)" in a single sentence
([ARCHITECTURE.md:60](docs/ARCHITECTURE.md#L60)), but never explains **how**
the two signals are combined into a single rank. There is no formula, no
statement of the default weights, and no worked example.

- **Expected:** A reader of the architecture doc can understand the scoring
  formula, the default vector/keyword weights, the normalization step, and
  see a concrete example of how a chunk's final score is computed — enough to
  reason about and safely tune retrieval ranking.
- **Actual:** The doc mentions blending but gives no formula or weights, so
  the only source of truth is the code itself.

This is a documentation gap, not a code bug — the retrieval logic is correct
and already implemented; it is simply undocumented. **Root cause:** the
architecture doc was written at a high level and the scoring detail was never
back-filled after `HybridRetriever` was implemented.

### Map

The fix touches one documentation file, but the *source of truth* for the
content is the retriever code:

- **File to edit:** `docs/ARCHITECTURE.md` — add a "Hybrid Retrieval Scoring"
  subsection under the RAG System section (around line 60).
- **Reference (read-only) — where the formula actually lives:**
  - `rag/retriever/hybrid.py` — `HybridRetriever.__init__` sets the defaults
    `vector_weight=0.7`, `keyword_weight=0.3`
    ([hybrid.py:13-14](rag/retriever/hybrid.py#L13-L14)); `retrieve()`
    normalizes each score set by its max and blends per chunk
    ([hybrid.py:57-90](rag/retriever/hybrid.py#L57-L90)), then filters by
    `min_score=0.3` and returns the top `max_chunks=10`.
  - `rag/retriever/keyword_search.py` — BM25 raw scores (`bm25_score`) that
    feed the keyword side.
  - `rag/retriever/vector_store.py` — vector similarity `score` that feeds
    the vector side.

### Plan

1. Read the retriever code carefully and extract the exact formula,
   normalization method, default weights, and post-blend filtering
   (`min_score`, `max_chunks`). (Done during reproduction.)
2. Draft a new "Hybrid Retrieval Scoring" subsection in `docs/ARCHITECTURE.md`
   stating: the formula
   `blended = vector_weight * norm(vector_score) + keyword_weight * norm(keyword_score)`,
   the defaults `0.7 / 0.3`, and that each score set is max-normalized to
   0–1 before blending.
3. Add a small worked example: sample raw vector + BM25 scores for two
   chunks, show the normalization, the weighted blend, and the resulting
   ranking, so the numbers are concrete.
4. Note the post-blend behavior (min_score threshold and top-k cutoff) and
   where the defaults are configured (`HybridRetriever` constructor args), so
   readers know how to tune them.
5. Proofread: confirm every number and default in the doc matches the code,
   and that internal references (file paths) are correct.

### Inputs & outputs

- **Input:** The current `HybridRetriever` implementation (the authoritative
  formula and defaults) and the existing `docs/ARCHITECTURE.md` structure.
- **Output:** An updated `docs/ARCHITECTURE.md` with a new scoring subsection
  containing the formula, default weights, normalization explanation, and a
  worked numeric example. No code behavior changes.

### Risks & unknowns

- **Doc drift:** If the weights or formula in `hybrid.py` change later, the
  doc could go stale. Mitigation: point readers to the `HybridRetriever`
  constructor as the source of the defaults rather than implying the doc is
  canonical.
- **Accuracy risk:** The worked example must match the code's actual
  normalization (max-normalization, not softmax or min-max). I confirmed it
  divides by the max of each score set — the example is built on that.
- **Scope creep:** Tempting to also document `min_score`/`max_chunks` tuning
  or the BM25 tokenizer; I'll keep it to what the issue asks (formula +
  weights + example) and mention the thresholds only briefly.

### Edge cases

The doc should acknowledge the states the code already handles, so readers
aren't surprised:

- A chunk found by **only** vector search or **only** keyword search — the
  missing side contributes 0 to the blend (code defaults the absent score to
  `0.0`).
- **All-zero scores** on one side — normalization guards against divide-by-zero
  (`if max > 0 else 0`), so the blend degrades gracefully to the other signal.
- The **min_score filter** dropping everything — the result list can legitimately
  be shorter than `max_chunks` (or empty).
