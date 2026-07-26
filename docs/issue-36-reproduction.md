# Issue #36 — Local reproduction notes

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)  
**Branch:** `docs/36-hybrid-retrieval-scoring`  
**Type:** Documentation gap (not a runtime crash)

## How to reproduce

1. Open `docs/ARCHITECTURE.md` → section **RAG System (`rag/`)**.
2. Observe it only says hybrid retrieval uses “vector similarity + BM25 keyword” — no formula, no weights, no threshold, no example.
3. Open `rag/retriever/hybrid.py` → `HybridRetriever.__init__` and `retrieve`.
4. Confirm the real scoring logic lives in code only:
   - defaults: `vector_weight=0.7`, `keyword_weight=0.3`
   - normalize each channel by its max score in the candidate set
   - `blended = vector_weight * vector_norm + keyword_weight * keyword_norm`
   - keep rows with `blended >= min_score` (default `0.3`), sort desc, truncate to `max_chunks`

## Observed gap (expected vs actual)

| | |
|---|---|
| **Expected** | Contributors can learn from ARCHITECTURE.md how ranking works and how to tune weights / `min_score`. |
| **Actual** | ARCHITECTURE.md is high-level only; scoring details exist only in `hybrid.py`. |

## Automated reproduction

```bash
pytest tests/unit/test_architecture_hybrid_docs.py -v
```

These three tests **failed during Week 8** while the docs gap existed. After the Week 9 `ARCHITECTURE.md` fix they should **pass**.

## Manual quote check (optional)

```bash
rg -n -i "hybrid|bm25|vector_weight|min_score|0\\.7|blend" docs/ARCHITECTURE.md
rg -n "vector_weight|keyword_weight|min_score|blended_score" rag/retriever/hybrid.py
```
