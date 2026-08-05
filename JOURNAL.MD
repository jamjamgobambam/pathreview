## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/147)]

**Issue title:** [Resume section detection fails on text with leading whitespace]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[`_detect_sections()` in resume_parser.py looks for section headers (Education, Skills, Experience, etc.) using patterns that require the header to sit at the very start of a line, with zero tolerance for leading spaces/tabs. PDF text extraction commonly preserves indentation, so real-world resume text almost always has some leading whitespace before headers — meaning detection silently returns an empty list instead of erroring, even though the sections are clearly there.]

What is "Section Detection" for?
when someone uploads a resume, the app scans the text looking for common section headers like Experience, Education, Skills, Projects, etc. It does this so it knows what sections to chunk based on different headers, "this chunk is skills, this is Experience". useful for context for later steps in the pipeline. 
The "whitespace" problem
Sections headers with literal leading whitespace, spaces, tabs, indentation, 

Education:              <- no leading spaces
- B.S. Computer Science

vs.

    Education:              <- 4 leading spaces before "Education"
    - B.S. Computer Science
we see that the second example has whitespace. 

Why whitespace breaks down and fails.
The code that looks for headers does something like "check if a line starts with exactly the word Education". That way of checing is strict and fails on whitespace. so even if there is a valid section header it will not detect it becaus of whitespace. 

**Branch name:** [fix/147-Resume-detection-fails-leading-whitespace]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/JMyoi/pathreview/commit/3a9a188]

**Reproduction summary:**
Ran the exact repro snippet from the issue against `ResumeParser.parse()` on indented text and confirmed `detected_sections` comes back as `[]` instead of `['Education', 'Skills']`. Also ran the three named failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) via `pytest tests/unit/test_resume_parser.py` and confirmed all three fail for the same reason: the section-header regexes in `_detect_sections()` (ingestion/parsers/resume_parser.py) anchor on `^`/`\n` with no allowance for leading whitespace, so indented section headers (common in both the test fixtures and real PDF-extracted text) never match.

**PLAN.md link:** [https://github.com/JMyoi/pathreview/blob/fix/147-Resume-detection-fails-leading-whitespace/PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: all four regex patterns in `_detect_sections()` (ingestion/parsers/resume_parser.py) now allow `[ \t]*` leading whitespace after the `^`/`\n` anchor. Confirmed via `git stash` comparison that this resolves exactly the 3 named failing tests from the issue plus `test_detect_sections`, with no regressions elsewhere in the file.

**Next steps:**
Add explicit edge-case tests per PLAN.md's "Edge cases" section (leading spaces, leading tabs, no-whitespace regression, mid-sentence false-positive guard, empty string), then run `make test-unit` and `make check` to confirm no new failures before opening the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/147-Resume-detection-fails-leading-whitespace`

**What you built:**
Updated the four section-header regex patterns in `_detect_sections()` to tolerate leading spaces/tabs (`[ \t]*` after the `^`/`\n` anchor), so indented section headers — the common case for PDF-extracted resume text — are now correctly recognized instead of silently returning an empty `detected_sections` list.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — no existing tests needed edits (the fix made them pass as-is); added 5 new tests: `test_detect_sections_with_leading_spaces`, `test_detect_sections_with_leading_tabs`, `test_detect_sections_no_leading_whitespace_still_works` (regression guard), `test_detect_sections_no_false_positive_mid_sentence`, and `test_detect_sections_empty_string`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands surface pre-existing, unrelated failures documented in the PR description; my changes introduce zero new failures in either — confirmed via before/after `git stash` comparison.)

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
harder than expected is going through and trying to understand and breakdown the large codebase, also writing all the plans and journals were a bit tedious before actually working on the issue.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
There are standards and specific rules you have to follow to collaborate in different codebases. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI tools helped me navigate the codebase and also break down the issue and underlying bugs and problems and helped me find a solution to the issue.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
not much I would change.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
Practicing industry best standards and going through all steps for collaboration.
