# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses regex patterns anchored at the start of a line (`^Experience`, `\nExperience`). When text is extracted from PDFs it commonly preserves leading indentation, so lines like `"    Education:"` never match those anchors. As a result, `detected_sections` comes back empty even when the resume clearly contains sections like Education and Skills. A successful fix would adjust the patterns to allow optional leading whitespace before section headers, so indented section names are detected correctly.

**Branch name:** fix/147-resume-section-detection-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### Is This Issue Right for Me? — Checklist Notes

**Part 1 — Understanding the issue:**
The issue is clear and reproducible. Running the exact snippet from the issue description confirms `detected_sections` returns `[]` when it should return `['Education', 'Skills']`. The expected behavior is equally clear: after the fix, indented section headers are detected correctly.

**Part 2 — Tier fit:**
Tier 1. The fix lives entirely in one method in one file (`ingestion/parsers/resume_parser.py`). No other modules are involved and no understanding of the broader system is required. I chose Tier 1 because this is my first contribution to this codebase.

**Part 3 — Codebase readiness:**
I located `_detect_sections()` in `ingestion/parsers/resume_parser.py` and read the full method. The patterns use `^` and `\n` anchors that do not allow leading whitespace. I also read the three named failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) in `tests/unit/test_resume_parser.py` end-to-end before claiming this issue.

**Part 4 — Scope and time:**
No blockers or dependencies. The fix is a targeted regex change — estimated 2–3 hours including tests and PR writeup. The issue has no open dependencies and is not blocked by any other issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
To reproduce issue #147, I ran pytest tests/unit/test_resume_parser.py. The section detection tests failed as expected. The current parsing logic anchors headers strictly to the start of a line, meaning it fails to identify valid headers like 'Experience' when they contain the leading indentations commonly left behind by PDF text extraction.

**PLAN.md link:** https://github.com/rcraig-2023/pathreview/blob/fix/147-resume-section-detection-whitespace/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the core implementation for Issue #147. I successfully updated the regex logic in `ingestion/parsers/resume_parser.py` to accurately detect PDF sections and strip out Markdown headers. I also rebuilt the local `.venv` virtual environment to resolve tooling configuration errors, ran `make test-unit` (confirming all 10 unit tests for `test_resume_parser.py` pass), and resolved the specific `ruff` linting errors for the files I touched via `make check`. 

**Next steps:**
Push my working branch to GitHub and open a draft Pull Request. I will document the pre-existing `make check` failures in the PR description as required by the contribution guidelines, and then request peer review in Slack. Once I receive and implement any necessary feedback, I will complete Check-In 2 and submit the final PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]
**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** 
[ ] make check passes  
[ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]