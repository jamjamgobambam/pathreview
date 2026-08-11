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

**Reproduction commit link:** [3a7f303](https://github.com/HwaejinChung21/pathreview/commit/3a7f303f6b92c3e27e3dd568aa7d52156f4e7a8a)

**Reproduction summary:**
I reproduced the bug at the parser level by running the same resume through `ResumeParser.parse()`
four ways — flush-left, space-indented, tab-indented, and indented markdown (`scripts/repro_issue_147.py`).
The flush-left version returns `detected_sections == ['Education', 'Experience', 'Skills']`, while all
three indented versions return `[]`, because every regex in `_detect_sections()` anchors the section
name directly to `^` or `\n` with no room for indentation. Four of the repo's existing resume-parser
tests already fail for this reason, and I added `TestSectionDetectionLeadingWhitespace` in
`tests/unit/test_resume_parser.py` to pin the behavior: three tests fail today and two guards
(flush-left control, no-false-positives) pass, so the suite proves the fix without over-broadening it.

**PLAN.md link:** [PLAN.md](https://github.com/HwaejinChung21/pathreview/blob/setup/147-resume-whitespace-fail/PLAN.md)

**Walkthrough video (recommended):** none

**Blockers or open questions:**
- The issue as written only names section detection, but an indented *markdown* resume also needs the
  line-anchored header strip in `_strip_markdown()` (`^#+\s+`) relaxed — relaxing detection alone
  leaves that case broken. I want to confirm the maintainer is happy with both changes in one PR.
- `tests/unit/test_resume_parser.py` has 5 failures and 3 lint errors on the branch before I touch
  anything. One failure (`test_strip_markdown_syntax`) is fixed by my change; the lint errors are
  unrelated unused imports. Leaving unrelated lint alone unless asked.
- Not sure whether non-breaking-space indentation from `pypdf` is common enough in real PDFs to be
  worth handling; noted in PLAN.md with the exact pattern I'd use if so.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented both PLAN.md sub-tasks in `ingestion/parsers/resume_parser.py`: whitespace-tolerant
`_detect_sections()` (`^[ \t]*…`) and indented-header stripping in `_strip_markdown()`. All 16 tests
in `tests/unit/test_resume_parser.py` pass, including the Week 8 reproduction suite and a new
compound-header guard (`Professional Experience` must not also match bare `Experience`). Removed
`scripts/repro_issue_147.py` so the PR stays focused on the fix + unit tests.

**Next steps:**
Open the PR against `ascherj/pathreview`, request peer/mentor feedback in Slack, and fill Check-in 2
with the PR link once the PR is ready for review.

**Blockers:**
`make check` / `make test-unit` still report many pre-existing failures unrelated to this issue
(repo-wide ruff noise, mypy stub issues, ~48 failing unit tests outside `test_resume_parser.py`).
Changes introduce no new failures in the resume parser suite (8 → 0 failures there).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/680

**Branch:** `setup/147-resume-whitespace-fail`

**What you built:**
`ResumeParser` now treats leading spaces/tabs before section headers as optional, so indented
plain-text and PDF-extracted resumes still populate `detected_sections`. Indented markdown headings
are stripped the same way so `## Experience` can be detected after `_strip_markdown()`.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — `TestSectionDetectionLeadingWhitespace` covers flush-left,
space-indented, tab-indented, indented markdown, mid-line false positives, and compound section
names. Existing resume-parser tests that previously failed due to indented fixtures now pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*(Scoped meaning for this repo: no new failures introduced by this change. Full-repo `make check`
and `make test-unit` still fail on pre-existing issues documented in the PR. `tests/unit/test_resume_parser.py`
is fully green: 16/16.)*

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
PR [#680](https://github.com/ascherj/pathreview/pull/680) is still open against `ascherj/pathreview`
with no maintainer comments or review approvals as of the Week 10 deadline. Summer 2026 cohorts do
not receive structured reviewer feedback through the course, so this was expected. I checked the PR
directly on GitHub before writing this entry.

**How you responded:**
N/A — no feedback to respond to yet. If comments arrive later, the first step would be to read each
one in context, reply with what I changed (or why I disagree), and push follow-up commits only where
the feedback points at a real gap — same approach I used when scoping the markdown-strip fix in
Week 8.

---

### Reflection

**What was harder than you expected?**
Tracing the bug to its *full* root cause, not just the line the issue named. Issue #147 pointed at
`_detect_sections()`, and relaxing the `^` anchor there was the obvious fix — but my reproduction
script showed indented *markdown* resumes still returned `detected_sections == []` even after that
change. I had to read `_strip_markdown()` and realize a second line-anchored pattern was undoing the
first fix. That coupling was not obvious from the issue title alone.

Separately, working in a repo where `make test-unit` and `make check` already fail on dozens of
unrelated tests made it hard to know what "green" meant. I spent real time distinguishing
pre-existing breakage from regressions I introduced, and ended up scoping my success criterion to
`tests/unit/test_resume_parser.py` (16/16) rather than the full suite.

**What did you learn about working in a large codebase?**
Production codebases carry history you did not write. The resume parser's four redundant regex
patterns, the fact that the HTTP upload endpoint bypasses `ResumeParser` entirely and calls `PyPDF2`
directly, and the `list(set(detected))` nondeterministic ordering — none of that was in the issue.
Before changing anything I had to map callers (`ingestion/pipeline.py`), read existing tests to
learn what behavior was already considered correct, and decide what was in scope. That is very
different from a personal project where you own every file and can refactor freely.

I also learned that a minimal diff is a form of respect. I deleted the Week 8 reproduction script
before opening the PR, resisted fixing unrelated lint in `test_resume_parser.py`, and documented
pre-existing failures in the PR description instead of trying to clean the whole repo. Upstream
maintainers review many PRs; staying focused makes yours easier to merge.

**How did AI tools help — and where did they fall short?**
AI was most useful for three things: (1) scaffolding the reproduction script and test class quickly
so I had failing tests before writing fix code, (2) drafting PLAN.md structure and regex
alternatives when I was stuck on `[ \t]` vs `\s` vs `\b`, and (3) navigating an unfamiliar Python
repo layout — finding `resume_parser.py`, its tests, and the ingestion pipeline without reading every
file manually.

Where AI fell short: it could not tell me whether non-breaking-space indentation from `pypdf` is
common in real PDFs, so I had to make a judgment call and document the `\xa0` gap in PLAN.md rather
than implement it blindly. It also initially treated the markdown-strip bug as optional until I ran
the reproduction and saw the indented-markdown case still fail — the tool suggested the obvious
one-line fix, but verifying *both* code paths required actually running the tests myself. AI
accelerates exploration; it does not replace reading the call chain and checking the output.

**What would you do differently if you started over?**
I would write the failing tests even earlier — before touching PLAN.md — and run them in all four
variants (flush-left, space, tab, markdown) on day one. That would have surfaced the `_strip_markdown()`
coupling sooner and saved a round of "fix detection, still broken" confusion.

I would also pick an issue whose bug is reachable through the running app if I wanted a stronger
end-to-end story. Knowing the resume-upload API never calls `ResumeParser` meant my reproduction
stayed at the unit-test level, which is correct for this issue but less satisfying than clicking
through the UI and seeing before/after behavior.

Finally, I would ask about maintainer scope preference earlier — whether the markdown-strip change
belongs in the same PR — instead of noting it only as an open question in Week 8.

**What are you most proud of from this module?**
Writing a reproduction that *proved* the bug before I wrote the fix. The four-variant table in
Week 8 (flush-left vs space vs tab vs indented markdown) made the defect concrete, gave me a test
suite that locked in the expected behavior, and caught the second root cause I would have missed if
I had jumped straight to editing regexes. That test-first habit — fail first, then fix, then confirm
no false positives — is the thing I want to carry into future contributions, more than any single
line of code in the PR.

