# PLAN.md — Fix for Issue #157

**Issue:** [#157 — Relevance scorer "partial overlap" test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)
**Branch:** `test/157-relevance-scorer-partial-overlap`

---

## 1. What needs to change

The unit test `test_query_with_partial_overlap` in
`tests/unit/test_relevance_scorer.py` is mislabeled: it claims to verify the
**partial-overlap** case (some query terms present in the chunk → a mid-range
score) but its fixture supplies a chunk containing **every** query term, so the
scorer correctly returns `1.0`. The test then asserts `0.3 < score < 0.9` and
fails against correct code.

**The target is the test fixture, not the production scorer.** The scorer in
`rag/evaluator/relevance_scorer.py` is correct and must stay untouched. A correct
fix makes the test a *genuine* partial-overlap case: the chunk should contain
only some of the query's tokens, so the computed score lands strictly inside
`(0.3, 0.9)` and the test passes for the right reason.

## 2. Parts of the codebase involved

| File | Role in this fix |
|---|---|
| `tests/unit/test_relevance_scorer.py` | **Edited.** Contains `test_query_with_partial_overlap` (the mislabeled fixture) at ~line 47. |
| `rag/evaluator/relevance_scorer.py` | **Read only — not edited.** `RelevanceScorer.score()` computes `overlap / len(query_tokens)`; `_tokenize()` does `text.lower().split()`. This is the behavior the fixture must exercise honestly. |
| `pyproject.toml` | Reference only — defines the `unit` pytest marker and ruff/black config the change must satisfy. |

## 3. How the scorer actually works (verified by reading the code)

`RelevanceScorer.score(query, chunks)`:
1. Tokenize the query: `set(query.lower().split())` → unique lowercase words.
2. For each chunk, tokenize its `text` the same way.
3. `overlap = len(query_tokens & chunk_tokens)`; `relevance = overlap / len(query_tokens)`.
4. Average the per-chunk relevances and clamp to `1.0`.

For the fixture's query `"Python Django web framework"`, `len(query_tokens) == 4`.
So the only scores possible for a single chunk are `0/4, 1/4, 2/4, 3/4, 4/4`
= `0.0, 0.25, 0.5, 0.75, 1.0`. To satisfy `0.3 < score < 0.9`, the chunk must
contain **exactly 2 or 3** of the 4 query terms.

## 4. Sub-tasks (step by step)

1. **Confirm the failure** — run
   `.venv/bin/pytest tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap -v`
   and observe `assert 1.0 < 0.9`. (Done in Week 8 reproduction.)
2. **Rewrite the fixture chunk** so it contains exactly 2 of the 4 query terms
   (`Python`, `Django`) and omits the other two (`web`, `framework`). Proposed
   replacement text: `"Django is a popular Python library for building applications"`.
   Expected score: `2/4 = 0.5`, which is strictly inside `(0.3, 0.9)`.
3. **Update the inline comment** on the assertion to state the intent explicitly
   (e.g. `# 2 of 4 query terms present -> 0.5`) so the fixture can't silently
   regress to full overlap again.
4. **Run the single test** to confirm it now passes.
5. **Run the whole file** — `.venv/bin/pytest tests/unit/test_relevance_scorer.py -v`
   — to confirm no sibling test regressed.
6. **Run the project gates** — `make test-unit` and `make check` (ruff + black +
   mypy) — to confirm the change meets contribution standards.
7. **Commit** on the working branch and open the PR against `ascherj/pathreview`.

## 5. Inputs / outputs and risks

**Inputs changed:** only the `chunks` fixture data inside one test function —
specifically the `text` value passed into `scorer.score(query, chunks)`. No
function signatures change; `score(query: str, chunks: list[dict]) -> float`
is untouched.

**Output changed:** the value `score` returned for this fixture moves from
`1.0` (full overlap) to `0.5` (2-of-4 partial overlap). The test's assertions
(`0.3 < score < 0.9`) are unchanged — they finally hold because the input is now
truly partial. No production output changes anywhere.

**Risks / unknowns:**
- *Wrong token count in the replacement chunk* (`tests/unit/test_relevance_scorer.py`):
  if the new text accidentally includes `web` or `framework`, the score returns to
  `0.75`/`1.0`; if it includes only 1 term, it drops to `0.25` and fails the lower
  bound. Mitigation: manually count overlap and run the single test before committing.
- *Tokenizer is whitespace-only and case-folding* (`_tokenize` in
  `relevance_scorer.py`): plurals/substrings like `frameworks` would NOT match
  `framework`, and punctuation stays attached to tokens. The replacement text must
  use clean, whole-word matches with no trailing punctuation.
- *Formatting gate* (`make check`): ruff/black run over the edited test file
  (mypy does not — its targets exclude `tests/`). Risk that reformatting touches
  the lines I edit. Mitigation: run `make format` then `make check`.
- *Unknown — hidden fixture coupling:* does any other test reuse this chunk? Read
  of the file shows each test defines its own local `chunks`, so the blast radius
  is one function. Re-running the full file in sub-task 5 verifies this.

## 6. Edge cases the fix must handle

1. **Score must be strictly inside the open interval `(0.3, 0.9)`.** With a
   4-token query the only safe single-chunk scores are `0.5` (2/4) and `0.75`
   (3/4). Boundary values `0.25` (1/4) and `1.0` (4/4) both fail. The chosen
   chunk yields `0.5`, comfortably away from both bounds.
2. **Case-insensitive matching.** The tokenizer lowercases, so `"Python"` in the
   chunk matches `"python"`-derived tokens. The replacement must not depend on
   capitalization to make (or avoid) a match — it must overlap on 2 terms
   regardless of case.
3. **No accidental extra matches via common words.** Filler words in the chunk
   (`is`, `a`, `for`, `building`) must not coincide with query tokens; verified
   that none of `{python, django, web, framework}` appear among them.
4. **No regression in sibling tests.** The other ~20 tests in the file
   (perfect-match, zero-overlap, empty inputs, whitespace-only, multi-chunk
   averaging) must still pass unchanged after the edit.

## 7. Definition of done

- `test_query_with_partial_overlap` passes because the fixture is genuinely partial.
- Full `tests/unit/test_relevance_scorer.py` passes (no regressions).
- `make test-unit` and `make check` both pass.
- PR opened against `ascherj/pathreview` with the template fully filled in.
