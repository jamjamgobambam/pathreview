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

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]