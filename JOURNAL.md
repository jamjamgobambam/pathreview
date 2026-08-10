# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue affects the safety layer of the application, specifically the PII scrubber that is responsible for detecting and redacting sensitive information. Currently, phone numbers written with parentheses around the area code, such as `(415) 555-1234`, are not detected and therefore remain visible. A successful fix will update the detection logic so these phone numbers are redacted while preserving the existing behavior for other supported phone number formats. I chose this issue because it has a well-defined scope and is a good first contribution to the project.

**Branch name:** fix/146-redact-parenthesized-phone-numbers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes ("Is this right for me?" checklist)

- [x] The issue has a clearly defined problem statement.
- [x] The expected behavior is easy to understand.
- [x] The issue appears to be limited to a small part of the safety layer.
- [x] I expect the fix to involve updating the phone-number detection logic and adding or updating tests rather than making large architectural changes.
- [x] I selected this issue because it is a Tier 1 issue and is appropriate for a first contribution to a larger codebase.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/hemasribavisetty/pathreview/commit/99e431f

**Reproduction summary:**
I reproduced the issue by locating the PII scrubber implementation in `safety/pii_scrubber.py` and reviewing the current phone number detection logic. I confirmed that the issue is related to the regular expression used for US phone numbers, which does not reliably handle phone numbers written with parentheses around the area code, such as `(415) 555-1234`. I also identified the related unit tests in `tests/unit/test_pii_scrubber.py` that will be used to validate the fix.

**PLAN.md link:**
https://github.com/hemasribavisetty/pathreview/blob/fix/146-redact-parenthesized-phone-numbers/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**
The backend setup exposed startup issues in the provided starter repository. Although the frontend and Docker services were configured successfully, the backend initialization encountered database startup issues. While waiting for guidance from the course staff, I continued analyzing the relevant code and prepared a detailed implementation plan for the assigned issue.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- Investigated the PII scrubber implementation.
- Identified the phone-number regular expression causing the issue.
- Planned the implementation.
- Updated the regex.
- Verified issue-specific tests.

**Next steps:**

Open the pull request, request review, and complete final testing.

**Blockers:**

The backend setup exposed unrelated startup issues in the starter repository, but they did not prevent implementation of Issue #146.

---

### Check-in 2 (end of week)

**PR link:**

<GitHub PR URL>

**Branch:**

fix/146-redact-parenthesized-phone-numbers

**What you built:**

Updated the US phone-number detection logic so that phone numbers written with parentheses around the area code are correctly detected and redacted. Existing supported US phone-number formats continue to work.

**Tests added or updated:**

Updated:

- tests/unit/test_pii_scrubber.py

Verified phone-number detection and redaction behavior.

**Self-review confirmation:**

- [ ] make check passes
- [ ] make test-unit passes

**Draft PR feedback received from:**

None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided during Summer 2026. I completed the contribution and submitted my pull request, but there were no maintainer review comments to respond to during this module.

**How you responded:**
No response or additional code changes were required because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**

The local development environment was more difficult to set up than I expected. I encountered several issues involving Python versions, Docker, PostgreSQL, and database initialization before I could focus on my selected issue. I also learned that debugging a failure in an unfamiliar repository requires separating problems caused by my own changes from problems that already exist in the codebase. During implementation, even a small regex change required careful testing because a pattern that fixes one input can potentially create false positives or affect other formats.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase is very different from building a project from scratch. Before changing anything, I needed to understand the repository structure, locate the relevant module, inspect existing tests, follow the project's contribution conventions, and keep my change narrowly scoped. For Issue #146, the actual implementation was relatively small, but understanding how `safety/pii_scrubber.py` interacted with the existing tests in `tests/unit/test_pii_scrubber.py` was an important part of making the change safely. I also learned the importance of recognizing unrelated or pre-existing failures rather than expanding the scope of a pull request to fix every problem encountered.

**How did AI tools help — and where did they fall short?**

I used ChatGPT throughout the contribution process to help navigate the unfamiliar repository, interpret error messages, reason about the phone-number regular expression, plan debugging steps, and organize my PLAN.md and JOURNAL.md documentation. AI was especially useful for explaining why the original regular expression could fail on a parenthesized phone number and for suggesting focused tests and edge cases. However, AI suggestions still had to be verified against the actual repository and test results. For example, running the full PII scrubber tests exposed an unrelated failure involving the street-address pattern, and I had to use the real test output to distinguish that existing behavior from the phone-number issue I was fixing. This reinforced that AI can accelerate investigation, but the codebase, tests, and observed behavior remain the source of truth.

**What would you do differently if you started over?**

I would spend less time trying to solve unrelated environment and starter-code problems before narrowing my attention to the specific issue I selected. I would also run the smallest relevant unit tests earlier instead of depending on the entire application to run end-to-end. For Issue #146, the behavior could be investigated directly through `PIIScrubber` and its unit tests without requiring every backend service to be operational. I would establish a baseline of relevant test failures first, make the smallest possible change, rerun the same tests, and only then expand to the broader test suite.

**What are you most proud of from this module?**

I am most proud of continuing through the full contribution workflow despite the setup and debugging challenges. I went from selecting an unfamiliar issue to locating the relevant implementation, reproducing and understanding the behavior, creating a structured solution plan, modifying the PII detection logic, testing the change, and preparing a pull request. More importantly, I became more comfortable working incrementally in someone else's codebase instead of treating every unexpected failure as something my contribution needed to fix.