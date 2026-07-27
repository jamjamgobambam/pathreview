## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/146](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The code used to hide sensitive personal information is currently missing a common phone number format: parenthesized US phone numbers. 

While it successfully catches numbers formatted with dashes (like 555-123-4567), it overlooks numbers written with parentheses (like (555) 123-4567). 

Because of this gap, parenthesized phone numbers slip through the system without being hidden or flagged as private data. A successful fix will make sure this standard phone number style is properly protected.

**Branch name:** [paste branch name here]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Is This Issue Right for Me?

### Part 1 — Understanding the Issue
- [x] Can I explain what this issue is asking for in my own words?
- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x] Do I understand which part of the app is affected?
- [x] I've located the relevant files and confirmed they exist in the codebase.
- [x] Do I understand what "done" looks like?
- [x] Can you describe what the app should do (or not do) once the issue is fixed? 
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

### Part 2 — Tier Fit
Issues in the tracker are tagged with a tier level. Here's what each one means:

#### Tier	Description	Typical scope
_Tier 1	Self-contained, localized fix. The change lives in one or two files and doesn't require understanding how the whole system fits together.	Bug fix, missing validation, broken test, documentation update_

_Tier 2	Requires understanding how two or more modules interact. May involve a service layer, database model, or API endpoint.	Feature addition, refactor, data flow bug_

_Tier 3	Requires understanding the full system — multiple modules, possibly infrastructure or AI pipeline changes.	Architecture change, cross-cutting behavior, RAG or agent modification_

- [x] Is the tier a realistic match for where I am right now?

### Part 3 — Codebase Readiness

_Can I find the relevant code?_

- [x] I've found and read the specific code the issue references (not just the file — the function or section).
Do I understand the surrounding code well enough to change it safely?
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- [x] I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- [x] Is the scope realistic for Weeks 8–9?
- [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
__[link to commit documenting the reproduced issue]__

[Commit 5d1ee4c](https://github.com/novamapp/pathreview/commit/5d1ee4ceb81ee16698571db448c00fed9eda3a2e)

**Reproduction summary:**
__[1–2 sentences: How did you reproduce the issue? What did you observe?]__

I went to the file (`pii_scrubber.py`) contacting the root of my chosen issue [#146](https://github.com/ascherj/pathreview/issues/146). I added the code in the `Steps to reproduce` section of my issue and ran the code to reproduce the issue.

I also ran the test file (`tests/unit/test_pii_scrubber.py`) mentioned in my selected issue and confirmed that the relevant tests are failing.

**PLAN.md link:** 
__[link to PLAN.md in your fork]__

[PLAN.md](PLAN.md)

**Walkthrough video (recommended):** 
__[link to your Loom video, ≤2 min — recommended, not graded]__

[walkthrough video](media/issue_walkthrough.mkv)

**Blockers or open questions:**
N/A