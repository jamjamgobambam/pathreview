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

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/791

**Branch:** `fix/151-expand-bias-detection-patterns`

**What you built:**
I expanded `BiasDetector` in `safety/bias_detector.py` so it recognizes more common dismissive educational-background phrasings and demographic assumptions, including `coding bootcamp` variants, plural age-based assumptions, and the issue example wording around bootcamp attendance and age. I preserved the existing detector interface, evaluation order, and public reason strings, and I added a boundary fix so terms like `insufficient` do not accidentally match inside larger words such as `insufficiently`.

**Tests added or updated:**
`tests/unit/test_bias_detector.py` was updated. The added and updated cases cover the Issue #151 examples, broader dismissive education and demographic phrasing variants, non-biased background-group mentions that should remain unflagged, and a regression proving that longer word forms like `insufficiently` do not trigger the educational-bias pattern by substring.

**Self-review confirmation:** [ ] make check passes [ ] make test-unit passes
`make check` still fails because of unrelated pre-existing repo-wide Ruff violations outside Issue #151. `make test-unit` still fails because of unrelated pre-existing unit test failures outside the bias detector work, but the targeted `tests/unit/test_bias_detector.py` run passed and the full unit run showed the bias detector tests passing.

Feedback updated

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No

**Summary of feedback:**
No formal reviewer feedback has been received on PR #791 yet, so I do not have maintainer comments to summarize at this stage.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was expanding the regex coverage in `safety/bias_detector.py` without making the detector too broad. Issue #151 looked small at first, but the existing tests and the new regressions showed that a simple keyword expansion would not be enough: I had to cover phrasing like `coding bootcamp graduates can't write enterprise code`, `self-taught developers are not equal to university graduates`, and `Given their age, they likely cannot keep up with modern frameworks`, while still not flagging neutral statements such as `your resume shows bootcamp attendance` or positive ones like `your bootcamp training has given you a solid foundation`. The follow-up boundary fix for `insufficient` versus `insufficiently` also made it clear that even a minor regex change can create subtle false positives if I do not test the exact wording carefully.

**What did you learn about working in a large codebase?**
I learned that even a narrowly scoped fix needs to respect the codebase's existing interfaces, conventions, and repository-wide behavior. In this case, `BiasDetector.detect_bias()` already returned a specific `(bool, reason)` tuple and the tests depended on the existing public reason strings, so the safest approach was to change pattern coverage rather than redesign the detector. I also had to separate issue-specific verification from repository baseline problems: my branch history and Week 9 notes show that `tests/unit/test_bias_detector.py` was the reliable source of truth for Issue #151, while `make check` and `make test-unit` still had unrelated pre-existing failures. That forced me to be precise about scope and not over-claim what my contribution fixed.

**How did AI tools help — and where did they fall short?**
AI tools helped most with speeding up pattern iteration and surfacing edge cases I should verify, especially around regex phrasing and boundary conditions. The branch history shows a follow-up commit, `92d75ff`, that addressed draft PR feedback, and the word-boundary regression for `insufficiently` is a good example of the kind of suggestion that was useful to investigate. But AI assistance was not enough on its own, because the real standard in this repository was the actual test file and the concrete branch history, not whether a pattern looked reasonable in isolation. I still needed to verify changes against `tests/unit/test_bias_detector.py`, confirm that neutral and positive phrases stayed unflagged, and avoid treating automated feedback as equivalent to formal reviewer approval.

**What would you do differently if you started over?**
If I started over, I would build a more explicit checklist from the failing and nearby test cases before editing the regexes, including positive, neutral, factual, and substring-regression cases. I eventually added that coverage in `tests/unit/test_bias_detector.py`, but doing it first would have made the implementation path clearer and probably reduced the need for follow-up refinement. I also would run the targeted bias-detector tests and record the repository baseline earlier in one place, because the unrelated `make check` and `make test-unit` failures mattered for how I interpreted later results and wrote the PR notes.

**What are you most proud of from this module?**
I am most proud that the final change stayed small and focused while still addressing the real gaps in Issue #151. Instead of broadening the detector indiscriminately, I expanded it in a way that matched the issue examples and common phrasings, added regression coverage for both biased and non-biased statements, and preserved the detector's existing interface and reason strings. The part that feels strongest to me is the combination of broader pattern support with guardrails like the `insufficiently` regression, because that shows I was not only trying to make more tests pass but also trying to keep the behavior responsible.
