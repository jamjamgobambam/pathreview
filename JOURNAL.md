## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser fails to detect section headers when the resume text contains leading whitespace, which commonly occurs in text extracted from PDFs. As a result, the parser returns an empty list of detected sections instead of identifying sections like "Education" and "Skills." A successful fix should allow section detection even when section headers are indented.

**Selection reasoning ("Is this right for me?"):**
I chose this issue because it has a clear reproduction case, a well-defined scope, and focuses on improving the resume parser without requiring changes across many parts of the codebase. It also provides related tests that will help verify the fix.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/6f3d37e7bb0677af652e40f5971b1256852571f8

**Reproduction summary:**
I reproduced the issue by using the provided resume parser example with resume text containing leading whitespace before section headers. The parser failed to detect the expected sections because _detect_sections() only matches section headers that begin at the start of a line.

**PLAN.md link:** (https://github.com/yaminik03/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md)

**Walkthrough video (recommended):** [Optional Loom link]

**Blockers or open questions:**
None at this time.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `_detect_sections()` in `ingestion/parsers/resume_parser.py`, updating the four detection regex patterns to allow optional leading whitespace (`[ \t]*`) before section headers, so indented headers from PDF-extracted text are now matched. Added 5 new unit tests in `tests/unit/test_resume_parser.py` covering leading spaces, tabs, mixed indentation, no-header text, and a regression check for unindented headers.

**Next steps:**
Run `make check` and `make test-unit`, confirm no new failures against the pre-fix baseline, open a draft PR for peer/mentor review, and finalize the JOURNAL.md and PR description.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/285)

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
Fixed `_detect_sections()` so its regex patterns accept optional leading whitespace or tabs before section header names, resolving the bug where indented section headers (common in PDF-extracted resume text) went undetected.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` — added `test_detect_sections_with_leading_spaces`, `test_detect_sections_with_leading_tabs`, `test_detect_sections_mixed_indentation`, `test_detect_sections_no_headers_still_empty`, and `test_detect_sections_unindented_unaffected`, covering the indentation edge cases from PLAN.md plus a regression check.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(177 pre-existing lint errors and 50 pre-existing test failures exist codebase-wide, none introduced by this change and none in the two files this PR touches beyond two pre-existing, unrelated `_strip_markdown()` failures — verified via `git stash` comparison. See PR description for details.)*

**Draft PR feedback received from:** ⚠️ none