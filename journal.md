## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/147)]

**Issue title:** [Resume section detection fails on text with leading whitespace]

**Tier:** [✓] Tier 1  [2173 ] Tier 2  [ ] Tier 3

**Problem summary:**

The current issue is that the section header in the pdf has a special character associated with it.
The parsing function uses the text extraction which preserves such special characters.
Due to this, the section may not be read properly or be read as blank.
Currently, check for such special character is missing and a successful fix would enable 
cleaner parsing of each section in the pdfs.
This bug can be spoted in the ingestion folder, in the resume_parser.py file.

**Branch name:** [fix/146-whitespace-detection]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger

**comment from owner** :_detect_sections() in resume_parser.py anchors every section-header pattern at the start of a line (^Experience, \nExperience). Text extracted from PDFs commonly preserves leading indentation, and for such input no sections are detected at all — detected_sections comes back empty.

Steps to reproduce:

from ingestion.parsers.resume_parser import ResumeParser
r = ResumeParser()
res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
print(res.metadata['detected_sections'])
observed: []  (expected: Education, Skills)

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [7d11d07](https://github.com/kishankc123/pathreview/commit/7d11d07e0568622f3f371316ef659602580e1179)

**Reproduction summary:**
I reproduced the owner-provided case locally with `.venv/bin/python`; parsing an indented resume string returns `metadata["detected_sections"] == []` instead of detecting `Education` and `Skills`. I also ran the focused resume parser tests and saw the same whitespace-sensitive failure pattern in the existing indented fixtures.

**PLAN.md link:** [PLAN.md](https://github.com/kishankc123/pathreview/blob/fix/146-whitespace-detection/PLAN.md)

**Walkthrough video (recommended):** Not recorded yet.

**Blockers or open questions:**
Need to confirm whether the final fix should preserve the current nondeterministic `list(set(...))` behavior or make section order deterministic while touching this parser.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: `_strip_markdown()` in `ingestion/parsers/resume_parser.py` now allows leading spaces/tabs before `#` headers (`^[ \t]*#+\s+`), fixing markdown header stripping on indented input. The `_detect_sections()` whitespace handling from the earlier reproduction commit was verified working, so I removed the now-stale `xfail(strict=True)` marker on `test_detect_sections_with_leading_whitespace_reproduction` in `tests/unit/test_resume_parser.py` — that test now passes for real instead of being expected to fail.

**Next steps:**
Run `make check` and `make test-unit` for a final self-review, then open the PR against `ascherj/pathreview` and request review.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [TODO: add link once PR is opened]

**Branch:** `fix/146-whitespace-detection`

**What you built:**
Fixed indented resume/markdown text losing its section headers: `_strip_markdown()` previously required `#` headers to start at column 0, so indented markdown (common in extracted PDF/triple-quoted text) never got its headers stripped; the regex now tolerates leading whitespace. Also confirmed the earlier `_detect_sections()` whitespace fix works and cleaned up the test that was still marked as an expected failure for it.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — removed the stale `xfail` marker on `test_detect_sections_with_leading_whitespace_reproduction`; `test_parse_markdown_resume` and `test_strip_markdown_syntax` now pass against the corrected regex.

**Self-review confirmation:** [✓] make check passes  [✓] make test-unit passes

**Draft PR feedback received from:** none