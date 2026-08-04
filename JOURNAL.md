## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** Tier 1

**Summary:**
PathReview’s bias detector currently uses regex patterns that require language to closely match a small number of predefined phrases. Because of this, the detector misses natural variations of dismissive statements about educational background and assumptions related to age. The problem affects the patterns and is demonstrated by nine failing tests. A successful fix will recognize the intended variations while keeping the patterns narrow enough to avoid flagging unrelated language.

**Selection notes**
This issue has a clearly identified implementation file, reproducible examples, and existing tests that define the expected behavior. Its scope is limited, so it does not require redesigning the application. I should be able to reproduce the failure and verify the solution using the provided unit tests.

**Branch name:** `fix/151-expand-bias-detection-patterns`

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rahp124/pathreview/commit/f10c4bfefdfd4e0773bf71dd1db7e58b58cb2140

**Reproduction summary:**
I reproduced the issue by running `tests/unit/test_bias_detector.py`, which produced nine failing test functions involving natural variations of dismissive educational language and demographic assumptions. The failing cases were:
`test_dismissive_bootcamp_language_detected`,
`test_bootcamp_lacks_rigor_detected`,
`test_demographic_assumption_age_detected`,
`test_coding_bootcamp_variant`,
`test_developer_vs_programmer_distinction`,
`test_multiple_bias_indicators`,
`test_negative_educational_claim`,
`test_rich_poor_assumption`, and
`test_assumption_vs_observation`.
I also ran the example from Issue #151 and confirmed the detector misses the intended phrasing, returning `(False, "")` for a statement that should be flagged.

**PLAN.md link:** [Link](https://github.com/rahp124/pathreview/blob/fix/151-expand-bias-detection-patterns/PLAN.md)

**Blockers or open questions:**
The main open question is how much flexibility to add to the regex patterns without causing positive, neutral, or factual references to educational backgrounds to be incorrectly flagged.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the reproduction and root-cause investigation for Issue #151 and documented the implementation approach in `PLAN.md`. The investigation confirmed that `safety/bias_detector.py` is still using narrow `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS`, which miss several common phrasings already covered by `tests/unit/test_bias_detector.py`. I also established the pre-change baseline on branch `fix/151-expand-bias-detection-patterns`: running `.venv/bin/python -m pytest tests/unit/test_bias_detector.py -q` produced `9 failed, 23 passed`, with the failing cases matching the Week 8 reproduction summary. Broader verification also showed unrelated pre-existing failures in `make check` and `make test-unit`, so implementation work is not complete yet.

**Next steps:**
Update the bias detector pattern coverage in `safety/bias_detector.py` while preserving the existing non-biased cases and reason strings. Re-run the targeted bias detector test file first, then run `make check` and `make test-unit` again to confirm the Issue #151 behavior after the code change and to separate any remaining unrelated failures from the bias-detector work. After verification, prepare the draft PR summary describing the implementation, baseline, and post-change test results.

**Blockers:**
There is an unrelated pre-existing repository baseline issue: `make check` currently fails during `ruff check .` with many existing lint violations outside Issue #151, and `make test-unit` also has unrelated pre-existing failures and environment-dependent network errors in chunker tests. These do not block targeted implementation in `safety/bias_detector.py`, but they do mean the full-project commands are not currently green before the fix.
