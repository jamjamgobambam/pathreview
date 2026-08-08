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


### Peer review feedback

**Reviewer:** @Daidai1031

**Feedback received:**
The reviewer asked me to restore the Summary and Issue headings, add manual reproduction steps, clarify the testing checkboxes, and explain why the unit-test and lint counts improved.

**Changes made:**
I updated the PR description to address all four points and marked the pull request ready for review.

**PR link:** https://github.com/ascherj/pathreview/pull/493

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No formal maintainer review feedback has arrived. For Summer 2026, formal reviewer feedback is not part of the module. I did receive peer feedback during Week 9 on my draft PR. The peer reviewer asked me to improve the PR description by restoring the Summary and Issue sections, adding manual reproduction steps, clarifying the testing checkboxes, and explaining why the unit-test and lint counts changed.

**How you responded:**
I updated the PR description to address the peer feedback, explained the before-and-after testing results more clearly, added a manual reproduction example, replied to the reviewer, and marked the pull request ready for review. I also documented the peer-review interaction in my Week 9 journal.

---

### Reflection

**What was harder than you expected?**
The hardest part was not the final regex change itself, but understanding whether failures were caused by my work or were already present in the repository. Before making the change, the full unit suite had 53 failures and the repository had 182 lint errors. I had to establish that baseline first and then compare it with the results after my fix. After the change, the four phone-related failures were fixed, my new regression test passed, and the full suite improved to 49 failures and 380 passing tests. This taught me that in an existing codebase, a failing command does not automatically mean my change is wrong. I also found the GitHub contribution workflow more involved than expected because I had to manage a feature branch, commits, a draft PR, peer review, and documentation in addition to writing the code.

**What did you learn about working in a large codebase?**
I learned that contributing to someone else's codebase requires much more discipline about scope. My issue was only about parenthesized US phone numbers, so I needed to avoid fixing unrelated lint errors or other failing tests even when I found them. I reproduced the bug first, traced it specifically to the `phone_us` regex in `safety/pii_scrubber.py`, wrote a plan, and made a focused change. I also learned why regression tests matter. A fix is stronger when there is a test that would fail if someone later reintroduced the same bug. Working in a shared repository also showed me that documentation, commit history, PR descriptions, and review comments are part of the engineering work, not separate from it.

**How did AI tools help — and where did they fall short?**
AI was most useful for helping me understand unfamiliar code, reason about the regular expression, interpret test and lint output, organize my debugging process, and understand Git and GitHub commands. It also helped me draft clear PR descriptions and professional review comments. However, I still had to verify everything myself by running the code and tests locally. For example, the repository already had many unrelated failures, so I could not simply assume that a command failing meant my implementation was incorrect. I needed to compare the baseline with the new results and inspect the actual failing tests. Reviewing other contributors' PRs also required looking at their real changes and running their focused tests rather than relying only on an AI explanation.

**What would you do differently if you started over?**
I would establish the repository baseline immediately after setup, before making any changes. That would make it easier to distinguish existing problems from problems introduced by my work. I would also read the contribution instructions and PR template earlier so I would know exactly what information the final PR needed. For the implementation itself, I would still choose a small Tier 1 issue, reproduce it first, and write focused tests before making broader changes. I would also keep the implementation diff as small as possible so automatic formatting does not create unnecessary unrelated changes.

**What are you most proud of from this module?**
I am most proud that I completed the full contribution process instead of only changing one line of code. I reproduced a real bug, identified the root cause, created a solution plan, implemented the fix, added a regression test, compared the repository before and after the change, created a pull request, responded to peer feedback, and reviewed other contributors' pull requests. The final code change was small, but I now understand much better how a real open-source contribution moves from an issue to a tested and reviewed pull request.


---
