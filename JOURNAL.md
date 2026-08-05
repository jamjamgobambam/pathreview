# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses
regex patterns anchored to the very start of each line (e.g. `^Experience`),
but text extracted from PDFs often keeps its original indentation, so headers
like "Education:" appear with leading spaces. Because the anchored patterns
never match indented headers, `detected_sections` comes back completely empty
for that input, and the resume content is never split into structured
sections. This also causes three unit tests in
`tests/unit/test_resume_parser.py` to fail. A successful fix would make the
matching tolerant of leading whitespace — for example by stripping/normalizing
lines before matching or allowing optional whitespace in the patterns — so
that sections are detected regardless of indentation and the failing tests
pass.

**Is this right for me? — reasoning:**
The problem is isolated to one method in one file, comes with a minimal
reproduction snippet, and already has failing unit tests that define exactly
what "fixed" looks like. No database, API, or frontend changes are involved,
so the scope is well contained and fits Tier 1.

**Branch name:** fix/147-resume-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #147. Updated the four regex patterns in
`_detect_sections()` (`ingestion/parsers/resume_parser.py`) to allow optional
leading whitespace before section headers, and applied the same fix to the
markdown header-stripping regex in `_strip_markdown()`, which had the same
root cause and was blocking section detection for indented markdown resumes.
Added `test_detect_sections_with_leading_whitespace`; all 11 tests in
`tests/unit/test_resume_parser.py` now pass, including two that were failing
on `main` (`test_parse_markdown_resume`, `test_strip_markdown_syntax`).
Verified the remaining 48 suite failures are pre-existing on `main` in
unrelated modules — the suite went from 54 failures to 48 with this change
and no new failures were introduced. Committed and pushed (`cc95774`);
draft PR opened and shared in Slack for peer review.

**Next steps:**
Address peer feedback on the draft PR, run final `make check` /
`make test-unit` verification, mark the PR ready for review, and complete
Check-in 2 with the PR link by Sunday.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [add your PR link here on Sunday]

**Branch:** `fix/147-resume-leading-whitespace`

**What you built:**
[fill in on Sunday]

**Tests added or updated:**
[fill in on Sunday]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, fill in on Sunday]