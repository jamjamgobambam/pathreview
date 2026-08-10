## Solution plan

**Issue:** Relevance scorer "partial overlap" test fixture actually has full query overlap — https://github.com/ascherj/pathreview/issues/157

### Understand

`RelevanceScorer.score` (`rag/evaluator/relevance_scorer.py:40-41`) scores a chunk
by the fraction of _query_ keywords it contains: `relevance = overlap / len(query_tokens)`.
A chunk that contains every query term therefore correctly scores `1.0`.

The unit test `test_query_with_partial_overlap` is named for partial overlap but its
fixture supplies **full** overlap: query `"Python Django web framework"` (tokens
`python, django, web, framework`) against chunk `"Django is a Python web framework for
rapid development"`, which contains all four tokens. The scorer returns `1.0`, but the
test asserts `0.3 < score < 0.9`, so `assert 1.0 < 0.9` fails.

- **Expected:** a partial-overlap fixture produces a mid-range score inside `0.3–0.9`.
- **Actual:** the fixture is total overlap, scorer returns `1.0`, assertion fails.

Root cause is the **test fixture**, not the scorer. The scorer behaves correctly.

### Map

- `tests/unit/test_relevance_scorer.py` (lines 47–60) — the failing test; **the only file to change.**
- `rag/evaluator/relevance_scorer.py` — scorer under test; **read-only, no changes.**
  Confirms the scoring formula and that `1.0` is correct for full coverage.

### Plan

1. In `test_query_with_partial_overlap`, edit the chunk `text` so it omits at least
   one query keyword — drop `"Python"`: `"Django is a web framework for rapid development"`.
2. Leave the query and all three assertions unchanged (they already express the
   intended partial-overlap contract).
3. Run `.venv\Scripts\pytest tests\unit\test_relevance_scorer.py -q` and confirm the
   file goes from `1 failed, 18 passed` to `19 passed`.
4. Update `JOURNAL.md` problem summary (done) and confirm no production code was touched.

### Inputs & outputs

- **Input:** query `"Python Django web framework"` and the edited chunk missing one term.
- **Output / change:** scorer now returns `3/4 = 0.75`, which satisfies `0.3 < score < 0.9`.
  Net effect: the previously failing assertion passes; no behavior change in shipped code.

### Risks & unknowns

- **Low risk** — a test-only, single-string edit. No production logic changes.
- Must keep the score strictly inside `(0.3, 0.9)`: dropping exactly one of four terms
  gives `0.75` (safe). Dropping two would give `0.5` (also valid) but the minimal change
  is preferred.
- No unknowns in the scorer's behavior; formula is confirmed by reading the source and
  by the captured log line `avg_score=1.0 query_len=4`.

### Edge cases

- The other tests in the file already cover empty query/chunks, whitespace-only chunks,
  missing `text` key, case-insensitivity, and very long inputs — all 18 pass and must
  continue to pass after the edit.
- Ensure the retained chunk still tokenizes to a non-empty set so it doesn't fall into
  the `relevances.append(0.0)` empty-chunk branch (`relevance_scorer.py:35-37`).
