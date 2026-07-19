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

