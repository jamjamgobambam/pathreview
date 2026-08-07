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


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
The part that I found harder was sticking to the contribution rules. I have usually worked in private repos and have used naming and messaging conventions as I would like.
Sticking to a specific format was challenging, I would have to remember the format or look it up. I did realize that following the standard conventions would make life much easier for the entire team.

**What did you learn about working in a large codebase?**
I learnt that navigating a large codebase can be easy once you have the habit of reading the documentation and following standard formats.

**How did AI tools help — and where did they fall short?**
AI tool were helpful in identifying edge cases of the bug I fixed. AI tools were pretty handy for me, and since I was working on a tier 1 issue, I received the help I needed from AI tools as needed.

**What would you do differently if you started over?**
I would change how I selected the issue. I could have been a bit more thorough while selecting the issue. I would also choose an issue that would push me to learn something new.

**What are you most proud of from this module?**
I am proud of how I was able to navigate the codebase, follow documentation and establish a good practice as a software developer.
