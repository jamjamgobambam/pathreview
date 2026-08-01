## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber can redact common phone-number formats, but it does not correctly detect US phone numbers that use parentheses around the area code. For example, a number such as `(555) 123-4567` may remain visible instead of being replaced. The problem appears to affect the phone-number pattern in `safety/pii_scrubber.py`. A successful fix will redact parenthesized phone numbers while keeping the currently supported formats working.

**Selection notes — Is this issue right for me?**
This issue has a focused scope and points to one main area of the codebase. It provides a clear example of the broken behavior and specific tests that can verify the solution. It is a Tier 1 issue, so it is appropriate for my current experience with contributing to a larger codebase. The issue should be manageable without requiring major architectural changes.

**Branch name:** `fix/146-parenthesized-phone-redaction`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ahmadzai38/pathreview/commit/47ef77d

**Reproduction summary:**
I reproduced the issue by passing `(555) 123-4567` and `555-123-4567` through `PIIScrubber`. The dashed number was redacted, but the parenthesized number remained visible, and `detect()` returned an empty list.

**Reproduction command:**

```powershell
@'
from safety.pii_scrubber import PIIScrubber

scrubber = PIIScrubber()

text = "Call me at (555) 123-4567 or 555-123-4567"

print("Original:", text)
print("Scrubbed:", scrubber.scrub(text))
print("Detected:", scrubber.detect("Call me at (555) 123-4567"))
'@ | .\.venv\Scripts\python.exe -
```

**Observed result:**

```text
Original: Call me at (555) 123-4567 or 555-123-4567
Scrubbed: Call me at (555) 123-4567 or [REDACTED]
Detected: []
```

**PLAN.md link:** https://github.com/ahmadzai38/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I still need to inspect the current phone-number regular expression and related tests before finalizing the solution plan.




## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I confirmed the baseline before changing the implementation. `make check` reports 182 existing lint errors, and `make test-unit` reports 375 passed and 53 failed. The failing unit tests include the parenthesized US phone-number cases from issue #146. I have reproduced the bug, traced it to the `phone_us` pattern in `safety/pii_scrubber.py`, and completed the solution plan.

**Next steps:**
I will update the US phone-number regular expression, run the focused PII scrubber tests, add or update regression tests if needed, and verify that the change introduces no new failures.

**Blockers:**
The repository already contains unrelated lint and unit-test failures. I will compare the results after my change against the recorded baseline.

---

### Check-in 2 (end-of-week)

**Current progress:**
I updated the `phone_us` regular expression so the PII scrubber now detects and redacts parenthesized US phone numbers such as `(555) 123-4567`. I also added a regression test confirming that the phone number is redacted while surrounding punctuation is preserved.

**Testing completed:**
- Phone-focused tests: `7 passed`
- Full PII scrubber tests: `25 passed, 1 pre-existing unrelated failure`
- Full unit-test baseline: `375 passed, 53 failed`
- Full unit-test result after the change: `380 passed, 49 failed`
- Repository lint baseline: `182 errors`
- Repository lint result after the change: `180 errors`

The four phone-related failures from the baseline now pass, and the new regression test also passes. The remaining failures are pre-existing and unrelated to issue #146.

**Self-review:**
- [x] The implementation is limited to the US phone-number regex.
- [x] A regression test covers the reported bug.
- [x] Existing supported phone formats still pass.
- [x] No new unit-test or lint failures were introduced.
- [x] The implementation commit was pushed to the feature branch.
- [x] Draft pull request created: https://github.com/ascherj/pathreview/pull/493

**Next steps:**
I will request peer feedback, address any relevant review comments, and mark the pull request ready for review.

**Blockers:**
The repository still has pre-existing unrelated unit-test, lint, and type-check failures. These results are documented in the pull request.

---
