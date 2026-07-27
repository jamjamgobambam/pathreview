## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/147)

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser’s section detection is too strict when it scans resume text in `ingestion/parsers/resume_parser.py`. Its header-matching patterns expect section names to start at the beginning of a line, so resumes with indented headings or leading whitespace can slip past detection. When that happens, common sections like Experience, Education, and Skills are missing from the parsed metadata even though the content is present. A successful fix would make section matching tolerant of leading whitespace so the parser recognizes standard resume layouts more reliably.

**Branch name:** setup/147-resume-whitespace-fail

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


### Part 1 — Understanding the Issue
Can I explain what this issue is asking for in my own words?
- yes

Do I understand which part of the app is affected?
- yes

I've located the relevant files and confirmed they exist in the codebase.
- yes

I can describe a concrete before-and-after: what the user sees before the fix and what they see after.
- yes

### Part 2 — Tier Fit
Choosing Tier 1 because this is my first open source contribution

### Part 3 — Codebase Readiness
I've found and read the specific code the issue references (not just the file — the function or section).
- yes

I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- yes

I've found the test file for my module and read at least one test end-to-end.
- yes

### Part 4 — Scope and Time
I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- yes

I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- yes

This issue has no open blockers or dependencies on other unresolved issues.
- yes

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** <!-- TODO: paste the commit URL after pushing, format: https://github.com/HwaejinChung21/pathreview/commit/<sha> -->

**Reproduction summary:**
I reproduced the bug at the parser level by running the same resume through `ResumeParser.parse()`
four ways — flush-left, space-indented, tab-indented, and indented markdown (`scripts/repro_issue_147.py`).
The flush-left version returns `detected_sections == ['Education', 'Experience', 'Skills']`, while all
three indented versions return `[]`, because every regex in `_detect_sections()` anchors the section
name directly to `^` or `\n` with no room for indentation. Four of the repo's existing resume-parser
tests already fail for this reason, and I added `TestSectionDetectionLeadingWhitespace` in
`tests/unit/test_resume_parser.py` to pin the behavior: three tests fail today and two guards
(flush-left control, no-false-positives) pass, so the suite proves the fix without over-broadening it.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** <!-- TODO: paste Loom link, or delete this line -->

**Blockers or open questions:**
- The issue as written only names section detection, but an indented *markdown* resume also needs the
  line-anchored header strip in `_strip_markdown()` (`^#+\s+`) relaxed — relaxing detection alone
  leaves that case broken. I want to confirm the maintainer is happy with both changes in one PR.
- `tests/unit/test_resume_parser.py` has 5 failures and 3 lint errors on the branch before I touch
  anything. One failure (`test_strip_markdown_syntax`) is fixed by my change; the lint errors are
  unrelated unused imports. Leaving unrelated lint alone unless asked.
- Not sure whether non-breaking-space indentation from `pypdf` is common enough in real PDFs to be
  worth handling; noted in PLAN.md with the exact pattern I'd use if so.

