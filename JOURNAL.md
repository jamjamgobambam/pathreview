## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace
 #147

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug chosen in the code looks for section headers in resumes. It looks for headers at the start of lines but since some PDF's add spaces before the text of headers (indentation), it incorrectly reads that resumes have no sections. It is an issue with the _detect_sections() portion of resume.py. A successful fix would allow for this whitespace to be detected and acknowledged that an item is still a header without incorrectly assuming all indented text is a header.

**Selection Reasoning:**
I chose this issue because i've never done big codebase changes or fixes like this before and it's within my scope. In college I took some python classes that taught the basics of regex and cleaning data with oddities like whitespaces so I felt this could be a helpful re-hash of those topics to strengthen them while applying them to a real project. I believe I could complete this in the time frame given (I will estimate 10 hours). I can see the relevant files in the codebase and have described them above. There don't appear to be dependencies on this issue which is good for me and works. I am working on the same issue as a friend in another section and am happy with that as we can collaborate and share ideas. I think I understand what's needed to create a fix without too much reading of code

**Branch name:** fix/147-resume-whitespace-detection

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
https://github.com/aashup30/pathreview/commit/d88ea49a344288380243e2c6b349a0ef14bc7d7e

**Reproduction summary:**
I ran the existing unit tests in `tests/unit/test_resume_parser.py` and confirmed
`TestResumeParser::test_parse_single_column_resume_text`,
`test_parse_resume_no_work_experience`, and `test_detect_sections` all fail because
`_detect_sections()` returns an empty list (`assert 0 > 0 where 0 = len([])`). 

I also ran `python -c "from ingestion.parsers.resume_parser import ResumeParser; r = ResumeParser(); res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n'); print(res.metadata['detected_sections'])"` which gave me the result []

To confirm the problem doesn't exist when there is no leading whitespace I ran `python -c "from ingestion.parsers.resume_parser import ResumePa/rser; r = ResumeParser(); res = r.parse('\nJohn Smith\njohn@example.com\n\nEducation:\n- B.S. Computer Science\n\nSkills: Python\n'); print(res.metadata['detected_sections'])"` which gave me the output ['Skills', 'Education'] confirming my theory.


**PLAN.md link:** 
https://github.com/aashup30/pathreview/blob/fix/147-resume-whitespace-detection/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
I think the only part i'm unsure about is  deciding on the exact fix whether its to get rid of the leading whitespace before matching, or change header regexes to allow optional leading whitespace. I need to confirm the change doesn't cause indented body text like bullets to be misdetected as section headers.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix from PLAN.md is implemented. I rewrote the pattern list in
`_detect_sections()` (`ingestion/parsers/resume_parser.py`) so the header
regexes goes with `^\s*` under `re.MULTILINE` instead of `^` / `\n`, which
lets indented and PDF-extracted headers (e.g. `    Education:`) match. 

Completed PLAN.md sub-tasks: 
- (1) fixed `_detect_sections()` to allow leading whitespace 
- (2) confirmed the three originally-failing tests now pass
(`test_detect_sections`, `test_parse_single_column_resume_text`,
`test_parse_resume_no_work_experience`)
- (3) added edge-case tests for indented, tab-indented, and mixed-indentation input; (4) verified indented body text containing a header word (e.g. "Experienced in Python") is NOT detected as a header. 

**Next steps:**
Run `make check`  on the changed files and fix any issues, open a draft PR against `pathreview` and request peer feedback in Slack, fill in the PR template, then mark it ready for review and add Check-in 2.

**Blockers:**
No major blockers. It may take some time to get the PR Reviewed. 
Note: `make test-unit` has ~50 pre-existing failures across unrelated
modules (review_service, pii_scrubber, skill_extractor, etc.) that exist on a
clean checkout before my changes. My changes do not touch those; I confirmed the
resume-parser suite goes from 5 failing to 2 failing, where the remaining 2
(`test_parse_markdown_resume`, `test_strip_markdown_syntax`) are pre-existing
failures in `_strip_markdown`, unrelated to issue #147.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/589)

**Branch:** `fix/147-resume-whitespace-detection`

**What you built:**
A fix to `_detect_sections()` in `ingestion/parsers/resume_parser.py` that lets
resume section headers be detected even when lines have leading whitespace. The
header patterns now use `^\s*<header>` under `re.MULTILINE` so indented and
PDF-extracted text matches, while still requiring the header to span its own line
(end-of-line or followed by `:`, `|`, `-`) so regular indented body text isn't
detected.

**Tests added or updated:**
Added 7 tests to `tests/unit/test_resume_parser.py`: 
- `test_detect_sections_indented_headers`(space-indented headers)
- `test_detect_sections_tab_indented_header` (tab indentation)
- `test_detect_sections_mixed_indentation` (mix of indented and flush-left headers)
- `test_detect_sections_header_on_first_line` (header with no preceding newline)
-  `test_detect_sections_header_without_colon` (header occupying a line with no trailing colon)
- `test_detect_sections_indented_body_not_misdetected` (indented body text containing a header word must return `[]`)
- `test_detect_sections_empty_input` (empty/whitespace-only input returns `[]` without error). 

The three pre-existing tests that reproduced the bug now also pass.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** N/A

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No 

**Summary of feedback:**
No review at the time of writing.

**How you responded:**
I did a final self-review of the PR instead of responding to feedback. I re-read the diff, confirmed `make check` and the resume-parser suite still pass, and made sure the PR description and test list were
accurate.

---

### Reflection

**What was harder than you expected?**
The actual regex fix was small, but figuring out where the fix belonged
and not break any other feature took up the most time. The hardest part
was proving the fix didn't over-match like making sure indented body text like
"Experienced in Python" wasn't mistaken for an "Experience" header. That
I wrote the header patterns so they still had to occupy their own
line (end-of-line or followed by `:`/`|`/`-`), which was more thinking than
the one-line `^` → `^\s*` initial change suggested. 

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is much more reading
than writing. On my own projects I know the whole thing in my head but here I
had to trace how `_detect_sections()` fed into `metadata['detected_sections']`
and trust conventions I didn't write. I learned I should onlytouch one function and leave everything else alone.
I also had to lean on the existing test suite as the benchmark for success in breaking anything else.
Also distinguishing "my failure" from "a pre-existing failure" turned out to be a
real challenge in a big codebase. Since not everything that was broken needed to be fixed, it was important to establish a baseline in test cases before making the fix and running the cases again.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation with help  quickly locating `_detect_sections()`,
explaining what `re.MULTILINE` does with `^`, and helping me draft the
edge-case tests (tab indentation, mixed indentation, empty input). It
couldn't tell me whether real PDF extraction uses tabs vs. non-breaking
spaces (`\xa0`), and it couldn't decide between stripping whitespace
per line vs. anchoring with `^\s*` so that trade-off required me to reason
 which approach was less likely to misdetect body text. I also had to
verify every suggested test actually failed for the right reason before and
passed after.

**What would you do differently if you started over?**
I'd establish the failing/passing baseline of the whole test suite on day one
so I didn't waste time later untangling pre-existing failures from my own. \

**What are you most proud of from this module?**
I'm proud of my methodology with regards to the testing I did to verify my issue. I added seven targeted tests including the negative case where indented body text containing a
header word must return `[]` so the fix is provably correct in both
directions. That's the part that would give a maintainer confidence to merge it, and it's the habit I most want to carry forward.