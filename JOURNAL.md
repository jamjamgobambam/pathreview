## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**"Is this right for me?" checklist reasoning:**
I selected the Tier 1 resume parser bug because it aligns well with my skill level for a first-time open-source contribution, and it has no open blockers, dependencies, or prohibitive contributor competition. I understood that the _detect_sections() function in ingestion/parsers/resume_parser.py incorrectly handles leading indentation/whitespace, causing empty sections to be detected. Fixing this will allow resume sections to be parsed accurately. I confirmed the file locations and reproduced the issue by running pytest on tests/unit/test_resume_parser.py. Three test cases, which were test_parse_single_column_resume_text, test_parse_resume_no_work_experience, and test_detect_sections, failed as expected due to this bug. Given the isolated nature of the bug and the clear test failures, I am confident I can resolve this ahead of the Week 9 deadline.

**Problem summary:**
The issue is the failure of the parser's section detection logic in ingestion/parsers/resume_parser.py. It expects the section headers to start exactly at the very beginning of the line. Because text extracted from PDFs preserves leading indentation or whitespaces, these headers are missed entirely, resulting empty sections detected. A successful fix will modify the regex patterns to allow leading whitespace before a header name, so that the parser can correctly identify and extract resume sections even when they are indented.

**Branch name:** fix/147-leading-whitespace

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Syoko3/pathreview/commit/1840b5738e8615099fe5e0be56bc7415ac64db5f

**Reproduction summary:**
I reproduced the issue by creating the detect_sections_bug.py to test the reproduction bug logic, and mark the _detect_sections() as a bug in ingestion/parser/resume_parser.py and the related failing tests in tests/unit/test_unit_parser.py. When I run the _detect_sections_bug.py, it returns an empty list, but the expected output has to return "Education" and "Skills" as the list. I also ran the unit tests for the parser again, and confirmed that section headers with leading whitespaces are not detected, so _detect_section() of resume_parser.py will return as an empty list.

**PLAN.md link:** https://github.com/Syoko3/pathreview/blob/fix/147-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix of the _detect_sections() of the ingestion/parsers/resume_parser.py by updating the regex of the section header patterns. After that, I confirmed the bug is fixed by running the unit test of the resume parser (tests/unit/test_resume_parser.py) to verify the three related failing tests are passed. I also ran the reproduction script and verified that the sections are correctly detected. I added the test cases for the leading whitespaces and the edge cases (.e.g. non-indented headers, substring words, etc.) in the test file, and verified that these tests also passed. I finished all of the sub-tasks from PLAN.md.

**Next steps:**
I have to open the draft pull request on GitHub and document pre-existing make check / make test-unit baseline failures in the PR description. I have to share the Draft PR link to the peer/mentor, and address any review feedback. I have to look the PR thread every day at least once. After addressing any review feedback, I have to update `JOURNAL.md` with Check-in 2, and mark PR as "Ready for review".

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [fix: allow leading whitespaces in resume section headers](https://github.com/ascherj/pathreview/pull/398)

**Branch:** fix/147-leading-whitespace

**What you built:**
My fix updates the line-start regex anchors in _detect_sections() of ingestion/parsers/resume_parser.py to match optional leading horizontal whitespace, which are `^[ \t]*` and `\n[ \t]*`. This allows section headers in indented resume text to be detected correctly, and it returns the list of detected sections instead of an empty list.

**Tests added or updated:**
I touched the tests/unit/test_resume_parser.py and they cover the existing section detection logic tests. I added 7 edge cases covering indented headers, non-indented headers, mid-sentence keywords, substring words, first-line headers, trailing whitespace, and section header deduplication.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
- `make check`: 178 pre-existing linting/formatting errors across the codebase. 0 new errors introduced in touched files.
- `make test-unit`: 2 pre-existing failures (`test_parse_markdown_resume` and `test_strip_markdown_syntax`) outside the scope of this issue since they are related to markdown syntax stripping. All 15 resume parser tests passed cleanly.

**Draft PR feedback received from:** [ru1nw](https://github.com/ascherj/pathreview/pull/398#pullrequestreview-4821888888)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [ ] No — still awaiting review

**Summary of feedback:**
My reviewer commented that it is ready to merge. He also commented on the checklist of the PR that verfied the codebase had no errors and ran as expected, fix ran as stated and related tests with edge cases handled correctly and passed, and the formatting of docs were correct.

**How you responded:**
I did not make any changes and just completed Week 9 Check-in 2 in this JOURNAL.md.

---

### Reflection

**What was harder than you expected?**
The harder part was the formatting of the PR description. I changed the title to a strong, specific one matching the example PR format, and I had to clearly document that the 178 `make check` errors and 2 `make test-unit` failures were pre-existing and outside my scope, so reviewers wouldn't mistake them for regressions I introduced.

**What did you learn about working in a large codebase?**
I learned that contributing to someone else's production code was to read the existing codebases, and then fix the bug or handle edge cases for the live users. I learned that this one includes the pull requests and code reviews. Building your own project was to choose your own tech stack and architecture, and execute full-lifecycle product development.

**How did AI tools help — and where did they fall short?**
I used AI assistance for the codebase navigation to understand the function and the bug of this issue that the given function has. They fell short at giving the steps to reproduce the bug using the code script from the issue link. I needed to create the reproduction bug script `detect_sections_bug.py`, so that I could see the observed output without fixing any code yet.

**What would you do differently if you started over?**
If I started over, I would test my regex patterns change in isolation before editing the source file by checking a single indented header against the pattern first. I placed the whitespace token in the wrong position (after the header word instead of after the line anchor), and a quick standalone check would have caught that immediately instead of after re-running the full suite.

**What are you most proud of from this module?**
One thing I am most proud of from this module is making my first real open-source contribution to someone else's production codebase and having it approved to merge with no requested changes. I learned the steps to contribute to someone else's production codebase and the format of the PR description, along with the commit message convention.
