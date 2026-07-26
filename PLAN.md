## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)

### Understand

**Root cause:** The hybrid ranking logic is implemented in code (`rag/retriever/hybrid.py`) but never documented in the architecture overview. `docs/ARCHITECTURE.md` only says the RAG system uses “vector similarity + BM25 keyword,” so contributors cannot tell *how* those scores become a final rank or what knobs exist.

**Expected vs actual:**
- **Expected:** ARCHITECTURE.md explains (1) per-channel max-normalization, (2) default weights `vector_weight=0.7` / `keyword_weight=0.3`, (3) the blended-score formula, (4) `min_score` filtering (default `0.3`), and (5) a short worked numeric example.
- **Actual:** RAG section is two high-level sentences; formula/defaults/example are missing. Automated reproduction tests in `tests/unit/test_architecture_hybrid_docs.py` fail for this reason (see `docs/issue-36-reproduction.md`).

**Formula as implemented today:**

```text
vector_norm  = raw_vector_score  / max(raw_vector_scores_in_candidate_set)
keyword_norm = raw_bm25_score    / max(raw_bm25_scores_in_candidate_set)
blended      = 0.7 * vector_norm + 0.3 * keyword_norm   # defaults
keep if blended >= 0.3                                   # default min_score
sort by blended desc; return top max_chunks
```

### Map

| File | Role |
|---|---|
| `docs/ARCHITECTURE.md` | **Primary edit** — add Hybrid Retrieval Scoring subsection under RAG System |
| `rag/retriever/hybrid.py` | Source of truth for formula, defaults, return fields (`score`, `vector_score`, `keyword_score`) |
| `rag/retriever/keyword_search.py` | BM25 channel (`bm25_score`); linked from docs for context |
| `rag/retriever/vector_store.py` | Vector channel (`score`); linked from docs for context |
| `tests/unit/test_architecture_hybrid_docs.py` | Reproduction / acceptance tests — should pass after docs land |
| `docs/issue-36-reproduction.md` | Week 8 reproduction notes (keep or fold into JOURNAL later) |

**Out of scope for this issue:** changing retrieval behavior, agent/frontend code, or adding new config knobs — docs-only Tier 1 fix.

### Plan

1. **Draft the scoring subsection** in `docs/ARCHITECTURE.md` under `### RAG System (`rag/`)`: purpose of hybrid search, formula, defaults, `min_score`, sort/truncate behavior.
2. **Add a worked example** with concrete numbers (e.g. vector raw/max → norm; BM25 raw/max → norm; blended; keep/drop vs `0.3`).
3. **Cross-link to code** — point readers to `HybridRetriever` in `rag/retriever/hybrid.py` (and briefly keyword/vector modules) so docs stay traceable.
4. **Verify acceptance** — re-run `pytest tests/unit/test_architecture_hybrid_docs.py -v` until all three tests pass; skim RAG section for clarity.
5. **Open PR** against upstream with issue #36 linked; update JOURNAL Week 9 when implementing.

### Inputs & outputs

**Inputs:**
- Existing implementation in `HybridRetriever.retrieve` / `__init__`
- Issue acceptance criteria (formula + defaults + example)
- Failing doc tests as the “definition of done” checklist

**Outputs / changes:**
- New prose (+ formula + example) in `docs/ARCHITECTURE.md` only (primary)
- Passing `tests/unit/test_architecture_hybrid_docs.py`
- No runtime behavior change

### Risks & unknowns

| Risk / unknown | Mitigation |
|---|---|
| Docs drift from code if weights change later | Cite `hybrid.py` defaults explicitly; keep example tied to current constructor signatures |
| Over-documenting internal helpers (`_get_all_chunks`) | Stick to scoring/ranking surface; don’t expand into full retrieval pipeline redesign |
| Possible keyword-path quirk: `retrieve()` calls `_get_all_chunks` but does not obviously call `keyword_searcher.index(...)` before `search` | Investigate only if needed for accurate wording; **do not expand #36 into a behavior bugfix** unless issue scope changes — note for office hours if keyword channel is empty in practice |
| Example numbers confuse readers if they assume absolute BM25 scale | Emphasize that normalization is relative to the **current candidate set’s max**, not a global constant |

### Edge cases

Document (or at least acknowledge in the example / caveats) that the implementation handles:

- **Missing from one channel:** chunk only in vector or only in keyword → other channel score treated as `0.0` before blending.
- **Empty candidate set / max = 0:** code uses `default=1.0` for max and guards `max > 0` when dividing — avoid divide-by-zero; blended may be `0` and drop under `min_score`.
- **Equal weights vs defaults:** constructor allows other weights; docs should label `0.7` / `0.3` as **defaults**, not hard-coded forever.
- **Threshold boundary:** `blended == 0.3` is kept (`>= min_score`); below is filtered out.
- **Tie / ordering:** results sorted by blended score descending; document that top-`max_chunks` are returned after filter.

---

*Living document — Week 9: ARCHITECTURE.md hybrid scoring subsection implemented; doc acceptance tests should now pass.*
