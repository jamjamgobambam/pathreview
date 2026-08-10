## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)

### Understand

`docs/ARCHITECTURE.md` describes the RAG System in a single sentence
(`docs/ARCHITECTURE.md:60`): *"Hybrid retrieval (vector similarity + BM25 keyword)
fetches relevant context from the user's ingested documents."* It never explains
**how** the two signals are scored, normalized, weighted, or combined into the
final ranking. A reader cannot understand or tune the retriever from the docs
alone.

- **Expected:** The architecture doc explains the hybrid scoring formula and the
  heuristic behind it — how vector and keyword scores are produced, normalized,
  weighted (defaults), blended into a single score, and filtered/ranked.
- **Actual:** Only the one-line mention exists; the formula lives solely in the
  code under `rag/retriever/`.

**Root cause:** Documentation debt — the retrieval implementation grew a specific
scoring heuristic, but `ARCHITECTURE.md` was never updated to describe it. This is
a docs-only issue; no runtime behavior is broken.

The actual formula, read from the code:

1. **Vector score** (`rag/retriever/vector_store.py:102-103`): ChromaDB returns a
   distance per result, converted to a similarity via `similarity = 1 / (1 + distance)`.
2. **Keyword score** (`rag/retriever/keyword_search.py:44-45`): raw `BM25Okapi`
   score from `rank_bm25` over whitespace-lowercased tokens.
3. **Per-signal max-normalization** (`rag/retriever/hybrid.py:58-59, 70, 76`): each
   score is divided by the max score in its own result set, mapping both signals to
   roughly 0–1 before blending.
4. **Weighted blend** (`rag/retriever/hybrid.py:14, 78-81`):
   `blended = vector_weight * vector_score + keyword_weight * keyword_score`,
   with defaults `vector_weight = 0.7`, `keyword_weight = 0.3`.
5. **Threshold + rank** (`rag/retriever/hybrid.py:29, 92-97`): drop results below
   `min_score` (default `0.3`), sort descending, return the top `max_chunks`.

### Map

Files I expect to touch:

- `docs/ARCHITECTURE.md` — **primary edit.** Expand the "RAG System (`rag/`)"
  subsection (around line 59-60) with a "Hybrid Retrieval Scoring" explanation
  and formula.

Files I will read as source-of-truth references (not edited):

- `rag/retriever/hybrid.py` — weights, max-normalization, blend formula, `min_score`
  threshold, ranking.
- `rag/retriever/vector_store.py` — distance→similarity conversion and the
  cosine-vs-euclidean question.
- `rag/retriever/keyword_search.py` — BM25 scoring and tokenization.

Possible (optional) addition:

- `docs/adr/` — a short ADR (e.g. `004-hybrid-retrieval-scoring.md`) if reviewers
  prefer the rationale to live as a decision record rather than inline. Decide in
  Week 9 based on feedback; default is inline in `ARCHITECTURE.md`.

### Plan

1. **Extract the formula from code** and write it in prose + a small formula block:
   normalization, `0.7·vector + 0.3·keyword`, and the `min_score`/top-`max_chunks`
   step, each cited to the file that implements it.
2. **Resolve the distance-metric ambiguity** (see Risks): confirm whether ChromaDB
   is using cosine (`hnsw:space: "cosine"` at `vector_store.py:37`) or euclidean
   (per the comment at `vector_store.py:102`), and document the similarity formula
   accurately — flagging the code/comment mismatch if it exists.
3. **Edit `docs/ARCHITECTURE.md`**: replace/expand the single sentence at line 60
   with a "Hybrid Retrieval Scoring" paragraph or subsection covering the two
   signals, normalization, default weights, blend, and threshold — plus the
   *heuristic* (why vector is weighted higher than keyword).
4. **Cross-check** the documented numbers/defaults against the code one more time
   and make sure any linked file paths/line references are correct.
5. **Self-review for accuracy and altitude** — keep it at architecture-doc level
   (formula + rationale), not a line-by-line code walkthrough; run any docs/link
   checks the repo has (`pre-commit`) before committing.

### Inputs & outputs

- **Input:** the existing `docs/ARCHITECTURE.md` and the three `rag/retriever/`
  modules as the authoritative description of the scoring behavior.
- **Output:** an updated `docs/ARCHITECTURE.md` whose RAG section documents the
  hybrid scoring formula (vector similarity conversion, BM25, max-normalization,
  `0.7/0.3` weighted blend, `min_score` threshold, top-`max_chunks` ranking) and
  the heuristic behind the weighting. No code or runtime behavior changes.

### Risks & unknowns

- **Distance-metric mismatch:** `vector_store.py:37` sets `hnsw:space: "cosine"`
  but `vector_store.py:102` comments distances are "euclidean by default" before
  applying `1 / (1 + distance)`. If I document the wrong metric the formula is
  misleading. Mitigation: verify empirically / from ChromaDB behavior in Week 9
  before finalizing; if the code and comment truly conflict, note it (and consider
  a follow-up issue) rather than silently picking one.
- **Docs drifting from code:** hard-coding `0.7/0.3` and `0.3` in prose risks
  going stale if defaults change. Mitigation: cite them as the current defaults in
  `HybridRetriever.__init__`/`retrieve` and reference the file so future readers can
  confirm.
- **Scope creep:** it's tempting to also document the generator/evaluator. Keep the
  change focused on the retrieval scoring formula that issue #36 names.
- **Over-detail:** turning an architecture overview into a code walkthrough. Keep it
  at the right altitude.

### Edge cases

The documentation should make the retriever's boundary behavior understandable:

- **Empty / unbuilt keyword index** (`keyword_search.py:40-42`): BM25 search returns
  `[]`, so results fall back to vector-only — the doc should note keyword is additive.
- **All scores below `min_score`** (`hybrid.py:92-93`): the retriever can legitimately
  return an empty list; document that `min_score` can filter everything out.
- **Zero / degenerate max scores** (`hybrid.py:58-59, 70, 76`): normalization guards
  against divide-by-zero (`if …_max > 0 else 0`); mention that a chunk found by only
  one signal still contributes via its weighted term.
- **Chunk present in only one result set** (`hybrid.py:63-76`): the union of vector
  and keyword IDs means a chunk missing from one signal simply scores 0 on that
  signal rather than being dropped.
