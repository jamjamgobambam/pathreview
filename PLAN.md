## Solution plan

**Issue:** #152 — Faithfulness checker can never mark short claims as supported
— https://github.com/ascherj/pathreview/issues/152

### Understand

The faithfulness checker scores how well generated feedback is grounded in the
retrieved context. `check()` splits the feedback into claims (sentences), then calls
`_is_supported(claim, context)` on each and returns the fraction that are supported.

**Root cause:** `rag/evaluator/faithfulness_checker.py`, `_is_supported()` ends with

```python
return len(meaningful_overlap) >= 2   # line 88
```

`meaningful_overlap` is the set of non-stop-word tokens the claim and context share.
The `>= 2` cutoff is an **absolute** threshold that ignores how long the claim is. A
short claim can carry fewer than two meaningful tokens, so it can never reach the
threshold — even when its key term appears in the context verbatim.

**Expected vs. actual (reproduced locally, see Week 8 journal):**

| Call | Actual (buggy) | Expected |
|---|---|---|
| `_is_supported("Is scalable", "The architecture is scalable and well-tested.")` | `False` | `True` — "scalable" is present verbatim |
| `check("Is scalable.", [{"text": "The architecture is scalable and well-tested."}])` | `0.0` | `> 0.0` |
| `check("The architecture is scalable and well-tested.", [same context])` | `1.0` | `1.0` (already works) |

The last two rows are the proof: identical wording scores `1.0` when long and `0.0`
when short. The score depends on claim length, not on whether the claim is grounded.

**What "done" looks like:** a genuinely grounded short claim is marked supported,
while an ungrounded claim (short or long) is still marked unsupported.

### Map

Files I expect to touch:

- **`rag/evaluator/faithfulness_checker.py`** — the fix lives here.
  - `_is_supported(claim, context)` (lines 66–88): replace the hardcoded `>= 2` with
    a length-aware rule. This is the single functional change.
  - `_extract_claims(text)` (lines 51–64): read-only context — note the
    `len(s.strip()) > 10` filter, which already drops the very shortest sentences and
    interacts with what reaches `_is_supported`.
  - `check(feedback, context_chunks)` (lines 12–49): read-only context — confirms the
    score is `supported / len(claims)`, so flipping one claim moves the score.
- **`tests/unit/test_faithfulness_checker.py`** — assertions.
  - Keep the two reproduction tests added this week
    (`test_short_grounded_claim_is_supported_issue_152`,
    `test_check_scores_grounded_short_feedback_above_zero_issue_152`).
  - Strengthen `test_minimum_overlap_required` (line 204) and
    `test_common_words_filtered_in_overlap` (line 192): they call `_is_supported`
    but only assert the return *type*, not the True/False verdict.

Out of scope (different root causes, confirmed while reproducing):
- `test_none_context_chunk_text` fails with a `TypeError` at line 34 — that is
  **issue #153** (None chunk text), not #152. I will not fix it here.

### Plan

1. **Baseline.** Run `.venv/Scripts/python -m pytest tests/unit/test_faithfulness_checker.py -v`
   and record which tests pass/fail before any change (2 repro tests fail by design; 4
   pre-existing failures noted under Risks).
2. **Compute the claim's meaningful-token count** inside `_is_supported`: build
   `claim_meaningful = set(claim.lower().split()) - stop_words` (reuse the existing
   `stop_words` set, factored out so claim and overlap use the same definition).
3. **Replace the threshold** with a length-aware rule. Primary candidate:
   `required = min(2, len(claim_meaningful))` then `return len(meaningful_overlap) >= required and len(meaningful_overlap) >= 1`.
   This keeps the `>= 2` behavior for normal claims but lets a claim whose only
   meaningful token is present count as supported. Evaluate a ratio-based alternative
   (`len(meaningful_overlap) / len(claim_meaningful) >= 0.5`) if `min()` over-credits.
4. **Guard the empty case:** if `claim_meaningful` is empty (claim is all stop words),
   return `False` and avoid any division.
5. **Add assertions** to the two currently-silent tests and confirm the two
   reproduction tests now pass.
6. **Run the file again**, then `make test-unit` (or the direct `pytest` command), and
   finally `make check` (ruff + black + mypy) to keep lint/format/types clean.

### Inputs & outputs

**Function changed:** `FaithfulnessChecker._is_supported(claim: str, context: str) -> bool`
— signature unchanged; only the decision logic changes.

- Input: a single claim string and the concatenated context string.
- Output: `True` if the claim's meaningful tokens are sufficiently represented in the
  context **relative to the claim's own length**, else `False`.

**Downstream effect:** `check()` returns `supported / len(claims)`, so a claim flipping
from unsupported → supported raises the score. No signature changes to `check()`.

**Test specification (already committed as failing tests this week):**

```python
def test_short_grounded_claim_is_supported_issue_152(self, checker):
    assert checker._is_supported(
        "Is scalable", "The architecture is scalable and well-tested."
    ) is True
```

### Risks & unknowns

1. **Over-crediting (main risk).** Loosening the threshold could mark *ungrounded*
   claims as supported. The regression guards are `test_feedback_with_no_support_in_context`
   (line 31) and `test_is_supported_without_keywords` (line 127) — both must still pass.
   I'll re-run them after the change.
2. **Which formula.** `min(2, n)` vs. a ratio is unresolved. Decision criterion: pick
   the one that makes the two reproduction tests pass *without* flipping the two
   no-support tests above. I'll try `min(2, n)` first and measure.
3. **Punctuation in tokenization (adjacent bug).** `_is_supported` tokenizes with
   `.split()`, so `"Python,"` (with a comma) does not match `"Python"`. This is why
   `test_multiple_context_chunks` (line 84) scores 0.0 today. A length-aware threshold
   alone may not fix that test — I need to decide whether stripping punctuation belongs
   in #152 or is a separate concern.
4. **Fragile pre-existing tests.** `test_partial_support_returns_middle_score` (line 43)
   and `test_multiple_claims_varying_support` (line 161) expect a *middle* score, but a
   single extracted claim can only score 0.0 or 1.0, and `_extract_claims`' `> 10`-char
   filter silently drops `"Knows Rust"`. These may not be fully fixed by the threshold
   change; I'll document whether they're in scope after investigating.

### Edge cases

- **Short, grounded claim** (`"Is scalable"` with "scalable" in context): must be
  supported. (Primary reproduction.)
- **Short, ungrounded claim** (`"Is scalable"` with a context that never says
  "scalable"): must remain unsupported.
- **Claim that is entirely stop words** after filtering (e.g. `"It is for the"`):
  `claim_meaningful` is empty — must return `False`, not divide by zero.
- **Long claim with only one overlapping token out of many**: should stay unsupported
  so we don't over-credit weakly-grounded long claims.
- **Case differences** (`"PYTHON SKILLS"` vs `"python skills"`): must still match —
  keep the existing `.lower()` normalization.
