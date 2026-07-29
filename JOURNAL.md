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
