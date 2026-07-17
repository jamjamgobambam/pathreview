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
