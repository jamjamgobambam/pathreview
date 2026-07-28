# Module 3 Journal — Shiven Saxena

## Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` builds regex patterns that look for section headers anchored immediately after a newline or at the start of a line — for example, `\nEducation:` or `^Skills`. Text extracted from PDFs frequently preserves the original indentation, so a line like `    Education:` (four leading spaces) never matches any of those patterns, and `detected_sections` comes back empty even when the section is clearly present. This means downstream components that rely on section metadata — such as chunking and relevance scoring — receive no structural signal from PDF-sourced resumes. A successful fix would update the patterns (or strip leading whitespace per line before matching) so that `Education`, `Skills`, and other headers are detected regardless of how much indentation precedes them.

**Selection notes (scope fit):**
Worked through the "Is this right for me?" checklist: the change is isolated to one private method (~20 lines) in a single file, the expected behavior is clearly defined by three failing unit tests in `tests/unit/test_resume_parser.py`, no external services or database are involved, and the fix requires only regex knowledge. Tier 1 / good first issue aligns with my comfort level entering this codebase.

**Branch name:** fix/147-resume-section-detection-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** PLACEHOLDER

**Reproduction summary:**
Ran `pytest tests/unit/test_resume_parser.py` locally with indented resume text (spaces before section headers); `test_detect_sections` and `test_parse_resume_no_work_experience` both failed with `assert 0 > 0` — `_detect_sections()` returned an empty list because none of the four regex patterns allow whitespace between the line-start anchor and the header word.

**PLAN.md link:** https://github.com/shivensaxena28/pathreview/blob/fix/147-resume-section-detection-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to verify that adding `\s*` before the header word in each pattern does not cause false positives on lines that happen to contain a section keyword mid-sentence (e.g. "She has experience with…").
