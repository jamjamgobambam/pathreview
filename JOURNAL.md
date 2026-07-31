# JOURNAL

## Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** ☑ Tier 1 ☐ Tier 2 ☐ Tier 3

### Issue-fit reasoning (Five Questions)

I chose this issue because it is a well-scoped Tier 1 bug that is appropriate for a first contribution to the PathReview codebase. Before selecting it, I verified that the affected function and related tests were clearly identified in the issue description, allowing me to understand both the current behavior and the expected outcome. The issue appears to be localized to the resume parser, making it realistic to complete within the Module 3 timeline while still providing experience reading and modifying an unfamiliar production codebase. There are no known blockers or dependencies, and the existing failing tests provide a clear starting point for reproducing and validating the fix.

### Problem summary

The resume parser currently fails to detect section headers when resume text contains leading whitespace, which commonly occurs after extracting text from PDF documents. Because the parser expects section headers to begin at the start of a line, valid headers such as "Education" and "Skills" are ignored when they are indented, resulting in an empty list of detected sections. A successful fix will allow the parser to recognize section headers even when leading whitespace is present while preserving the existing behavior for correctly formatted resumes.

**Branch name:** `fix/147-resume-section-whitespace`

**Setup confirmation:** ☑ App runs locally at localhost:5173

**Cohort ledger:** ☑ Issue added to cohort ledger

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:**
*To be updated after the reproduction commit is created.*

**Reproduction summary:**

I reproduced Issue #147 by running the existing resume parser unit tests in my local development environment. The three tests referenced in the GitHub issue (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, and `test_detect_sections`) all failed because `_detect_sections()` returned an empty list for resume text containing indented section headers. During investigation I also observed unrelated failures involving `_strip_markdown()`, which currently appear to be outside the scope of this issue.

**PLAN.md link:**
*To be updated after PLAN.md is committed.*

**Blockers or open questions:**

At this stage I believe the issue is localized to `_detect_sections()`, but I still need to confirm the smallest implementation that preserves all existing section-detection behavior while supporting leading whitespace.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Implemented the fix for Issue #147 by updating the resume parser to detect section headers with leading whitespace. Verified the existing regression tests covering this behavior now pass and completed project-wide validation to confirm no additional failures related to this issue were introduced.

**Next steps:**

Open a pull request, complete the project documentation, and respond to any reviewer feedback if received.

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/283

**Branch:**

`fix/147-resume-section-whitespace`

**What you built:**

Updated the resume parser to correctly detect resume section headers that contain leading whitespace, which commonly occurs after PDF text extraction. The implementation was intentionally limited to the section detection logic to keep the fix scoped to Issue #147.

**Tests added or updated:**

No new tests were added because the existing regression tests already covered this behavior. Verified that the targeted resume parser regression tests now pass.

**Self-review confirmation:**

Project-wide validation completed by running:

- `make test-unit`
- `make lint`
- `make typecheck`

The repository contains pre-existing unrelated test, lint, and type-check failures outside the scope of Issue #147. No additional failures related to resume section detection were introduced by this change.

**Draft PR feedback received from:**

None.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback arrived by the submission deadline. This is expected for the Summer 2026 offering of AI201.

**How you responded:**

N/A.

---

### Reflection

**What was harder than you expected?**

I expected writing the code to be the hardest part, but it actually wasn't. The biggest challenge was figuring out where the bug was coming from in a codebase I'd never worked in before. Once I took the time to understand how `resume_parser.py` handled section detection, the actual fix for Issue #147 ended up being much smaller than I originally expected.

**What did you learn about working in a large codebase?**

This project taught me that understanding the existing code is usually more important than writing new code. Instead of immediately trying to change things, I learned to follow the existing patterns, keep my implementation focused, and only modify what was necessary to solve the issue. That approach made it much easier to reason about my changes and explain them in my pull request.

**How did AI tools help — and where did they fall short?**

AI saved me a lot of time when I was trying to understand parts of the project that were unfamiliar, and it was especially helpful for talking through different approaches and reviewing my work before I committed it. At the same time, I learned that I couldn't rely on the first solution it suggested. Sometimes it wanted to jump into implementation before we had fully confirmed the root cause, so I still had to slow down, investigate the code myself, and make sure the change actually addressed the problem.

**What would you do differently if you started over?**

If I started over, I'd spend more time investigating before thinking about solutions. Looking back, the more I understood how the existing code worked, the easier every later step became, from writing the fix to testing it and explaining it in the PR. I'd also feel much more comfortable navigating an unfamiliar codebase now than I did at the beginning of the module.

**What are you most proud of from this module?**

I'm most proud of making my first contribution to a real open-source project. Before this module, contributing to someone else's codebase felt intimidating, but now I understand the entire workflow—from investigating an issue and making a focused change to creating a professional pull request. It gave me confidence that I can contribute to real projects outside of class.
