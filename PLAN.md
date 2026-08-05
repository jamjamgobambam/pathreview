## Solution plan

**Issue:** [#157 — Relevance scorer "partial overlap" test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Bug replication

1. Run `.venv/bin/pytest tests/unit/test_relevance_scorer.py -q`
2. Observe: `1 failed, 18 passed` — failure is `TestRelevanceScorer::test_query_with_partial_overlap`
3. Assertion failure: `assert 1.0 < 0.9` at `tests/unit/test_relevance_scorer.py:60`, with logged `avg_score=1.0`

Confirmed locally (2026-07-21).

### Understand

`RelevanceScorer.score()` (`rag/evaluator/relevance_scorer.py`) computes relevance as keyword-overlap ratio: `overlap / len(query_tokens)`, where overlap is the set intersection of lowercased, whitespace-tokenized words from the query and the chunk text.

`test_query_with_partial_overlap` intends to exercise the case where only *some* query terms appear in a chunk, asserting the resulting score lands in `0.3 < score < 0.9`. But the fixture data is wrong:

- Query: `"Python Django web framework"` → tokens `{python, django, web, framework}`
- Chunk: `"Django is a Python web framework for rapid development"` → contains all 4 query tokens

Every query token is present in the chunk, so overlap is 4/4 = 1.0 (full match), not partial. The scorer is behaving correctly per its own logic (full overlap → 1.0); the test fixture just doesn't represent "partial overlap" as its name and docstring claim. This is a test-fixture bug, not a scorer bug — no production code in `rag/evaluator/relevance_scorer.py` needs to change.

**Expected vs. actual:**
- Expected: chunk text omits at least one query term, so the assertion validates the partial-overlap code path (some but not all tokens matching).
- Actual: chunk contains every query term, so the assertion accidentally checks the full-overlap path and fails.

### Map

Files expected to touch:

- `tests/unit/test_relevance_scorer.py` — only file requiring a change. Specifically the `chunks` fixture text (line 52) inside `test_query_with_partial_overlap` (lines 47–60).

Files read/verified but NOT expected to change:

- `rag/evaluator/relevance_scorer.py` — confirmed scorer logic is correct as-is; no fix needed here.

### Plan

1. Edit the chunk text in `test_query_with_partial_overlap` so it contains some but not all query terms — e.g. drop "Django" and/or "framework" from the chunk so only a subset of `{python, django, web, framework}` is present.
2. Manually compute the expected overlap ratio for the new fixture to confirm it lands inside `0.3 < score < 0.9` before running the test (so the assertion range doesn't need adjusting too).
3. Run `.venv/bin/pytest tests/unit/test_relevance_scorer.py -v` and confirm `test_query_with_partial_overlap` now passes and all other 18 tests still pass (no regressions from the edit, since only one fixture changes).
4. Run the full unit suite (`make test-unit`) to confirm no other test depends on this fixture's current text.
5. Update `JOURNAL.md` / commit with a Conventional Commit message, e.g. `test(rag): fix partial-overlap fixture in relevance scorer tests`.

### Inputs & outputs

- **Input:** the `query` string and `chunks` list literals inside the single test function.
- **Output:** a chunk text string that genuinely omits ≥1 query token, causing `scorer.score()` to return a value strictly between 0.3 and 0.9, so the existing assertions pass without weakening them.

### Risks & unknowns

- Need to pick chunk wording that lands the score comfortably inside `(0.3, 0.9)`, not just barely over/under a boundary — a token count that's too sparse could drop below 0.3, or still include too many terms and stay near 1.0. Will hand-verify the overlap ratio before running.
- The `RelevanceScorer._tokenize` implementation is a naive `.lower().split()` — no punctuation stripping — so wording like "Django," or "framework." would tokenize as `django,`/`framework.` and silently fail to match. Need to keep the omitted/kept terms as clean whitespace-delimited words.
- Should confirm no other test or non-test code (e.g. `rag/evaluator/eval_suite.py`, `scripts/run_evals.py`) imports or relies on this specific fixture string — a quick grep for the chunk text confirms it's local to this one test.
- Low risk overall: change is isolated to one test fixture, no production code or public API changes, so blast radius is minimal.

### Edge cases

Not applicable in the traditional sense — this is a test-fixture-only fix, not new production logic. The main "edge case" to guard against is picking replacement fixture text that:
- still contains ≥1 but not all 4 query tokens (must genuinely be "partial"),
- doesn't accidentally match 0 tokens (would test the zero-overlap path instead),
- doesn't rely on substring/stemming behavior the tokenizer doesn't implement (e.g. "frameworks" ≠ "framework" under naive `.split()`).
