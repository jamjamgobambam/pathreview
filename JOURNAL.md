## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser fails to detect section headers when the input text contains leading whitespace, which is common in text extracted from PDFs. The _detect_sections() function only matches headers that begin at the very start of a line (e.g., ^Education), so indented headers like Education: or Skills: are ignored. As a result, detected_sections is returned as an empty list even though valid sections are present.

**Branch name:** fix/147-resume-parsing-breaks-on-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/karthikkatu/pathreview/commit/bd52bb4

**Reproduction summary:**
Wrote a minimal test feeding `_detect_sections()` resume text with indented section headers (e.g. `        Education:`) — it returned an empty list instead of detecting "Education" and "Skills", confirming the regex patterns don't tolerate leading whitespace. Notably, 5 pre-existing tests in the suite were already failing for the same reason without anyone noticing.

**PLAN.md link:** https://github.com/karthikkatu/pathreview/blob/fix/147-resume-parsing-breaks-on-whitespace/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
`_strip_markdown()`'s header-stripping regex (`^#+\s+`) has the same whitespace-anchoring flaw and causes one more pre-existing test failure (`test_strip_markdown_syntax`) — planning to leave it out of scope for #147 and flag it as a separate follow-up issue rather than bundling an unrelated fix into this PR. Also unconfirmed: whether real PDF extraction ever emits non-space whitespace (e.g. non-breaking spaces) before headers, since I've only tested against synthetic text fixtures so far.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: `_detect_sections()`'s four regex patterns now allow `[ \t]*` after each `^`/`\n` anchor, so indented section headers are detected. Ran the full `make test-unit` suite before and after the change — the 4 tests tied to issue #147 (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`, `test_detect_sections_with_leading_whitespace`) flip from failing to passing, and no other test in the 429-test suite changed status (diffed the full failure list before/after to confirm). Also added 3 new edge-case tests per PLAN.md: tabs-only indentation, a false-positive guard (section keyword appearing indented mid-sentence, not as a header), and empty-string input. That covers PLAN.md sub-tasks 1-3.

**Next steps:**
Sub-task 5 (final `make check` self-review) is next, then filling in the PR template and opening a draft PR for peer/mentor feedback in Slack before marking it ready for review.

**Blockers:**
`make check`/`make test-unit` surface a large number of pre-existing failures unrelated to this fix (54 failing unit tests repo-wide, 179 ruff lint errors, and a handful of mypy import-stub errors) — none in files this PR touches except two pre-existing lint issues in `resume_parser.py` itself (import ordering, one `raise ... from e` warning I fixed in passing since the file was already open) and the `_strip_markdown` bug noted in Week 8. Documenting the full pre-existing-failure baseline in the PR description so reviewers can see this change introduces nothing new.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/147-resume-parsing-breaks-on-whitespace`

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]