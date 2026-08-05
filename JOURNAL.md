# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `ingestion/parsers/resume_parser.py` uses
regex patterns anchored to the very start of each line (e.g. `^Experience`),
but text extracted from PDFs often keeps its original indentation, so headers
like "Education:" appear with leading spaces. Because the anchored patterns
never match indented headers, `detected_sections` comes back completely empty
for that input, and the resume content is never split into structured
sections. This also causes three unit tests in
`tests/unit/test_resume_parser.py` to fail. A successful fix would make the
matching tolerant of leading whitespace — for example by stripping/normalizing
lines before matching or allowing optional whitespace in the patterns — so
that sections are detected regardless of indentation and the failing tests
pass.

**Is this right for me? — reasoning:**
The problem is isolated to one method in one file, comes with a minimal
reproduction snippet, and already has failing unit tests that define exactly
what "fixed" looks like. No database, API, or frontend changes are involved,
so the scope is well contained and fits Tier 1.

**Branch name:** fix/147-resume-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #147. Updated the four regex patterns in
`_detect_sections()` (`ingestion/parsers/resume_parser.py`) to allow optional
leading whitespace before section headers, and applied the same fix to the
markdown header-stripping regex in `_strip_markdown()`, which had the same
root cause and was blocking section detection for indented markdown resumes.
Added `test_detect_sections_with_leading_whitespace`; all 11 tests in
`tests/unit/test_resume_parser.py` now pass, including two that were failing
on `main` (`test_parse_markdown_resume`, `test_strip_markdown_syntax`).
Verified the remaining 48 suite failures are pre-existing on `main` in
unrelated modules — the suite went from 54 failures to 48 with this change
and no new failures were introduced. Committed and pushed (`cc95774`);
draft PR opened and shared in Slack for peer review.

**Next steps:**
Address peer feedback on the draft PR, run final `make check` /
`make test-unit` verification, mark the PR ready for review, and complete
Check-in 2 with the PR link.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/902

**Branch:** `fix/147-resume-leading-whitespace`

**What you built:**
Fixed resume section detection failing on text with leading whitespace
(issue #147). Added optional leading whitespace to the header-matching
regexes in `_detect_sections()` and to the markdown header-stripping regex
in `_strip_markdown()` — the same root cause existed in both places — so
indented headers from PDF-extracted and markdown resumes are now detected,
while column-0 headers continue to work with no regression.

**Tests added or updated:**
Modified `tests/unit/test_resume_parser.py`: added
`test_detect_sections_with_leading_whitespace`, which verifies that section
headers preceded by spaces (e.g. indented "Education:" and "Skills:") are
detected. Also added type annotations to the existing tests (required by the
mypy pre-commit hook). Two previously failing tests in this file now pass:
`test_parse_markdown_resume` and `test_strip_markdown_syntax` (indented
markdown headers are now stripped and detected). Full file: 11/11 passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(no new failures introduced beyond the failures pre-existing on `main` —
48 test failures and 178 lint errors in unrelated modules, documented in the
PR description; both changed files pass ruff, black, and mypy)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in on PR #902 before the end of the module
(reviewer feedback is not a feature this term).

**How you responded:**


---

### Reflection

**What was harder than you expected?**
The gap between "I have the fix" and "the fix is actually in my repo."
At one point I was sure the code change was done — I had the corrected
file open and had even shared it — but when I ran `grep` on the actual
file on disk, the old buggy regex was still there. My branch only had
documentation commits. Nothing was wrong with my understanding of the
fix; the problem was that I never verified what was actually saved and
committed. Debugging that taught me more than writing the fix did.

**What did you learn about working in a large codebase?**
That my change doesn't exist in isolation. When I ran the test suite
and saw 54 failures, my first instinct was panic — but most of those
failures existed on `main` before I touched anything. I had to run the
suite on both branches and diff the results to prove my change
introduced zero new failures (and actually fixed two pre-existing
ones). I also learned that one bug can live in more than one place:
the leading-whitespace problem from issue #147 existed in
`_detect_sections()` AND in `_strip_markdown()`, and fixing only the
reported one would have left markdown resumes still broken. The
pre-commit hooks (ruff, black, mypy) blocked my commits repeatedly
until my files met the project's standards — in a shared codebase, the
tooling enforces conventions whether you like it or not. I also
accidentally overwrote `readme_parser.py` with a bad paste and broke
test collection for the whole suite; `git status` and `git restore`
saved me, which showed me how much blast radius a careless edit has in
someone else's code.

**How did AI tools help — and where did they fall short?**
AI helped me debug, check my code, and understand the structure of the
codebase and the contribution workflow — things like why pre-commit
hooks abort a commit after auto-fixing, and how to classify
pre-existing test failures. Where it fell short: the AI can only see
what I show it. It "verified" a fixed version of my file that turned
out to never exist in my repo — the real state of my code was only
visible through `git status`, `git diff`, and `grep` on my own
machine. The lesson is that AI output isn't done until I've verified
it against the actual filesystem and test runner myself.

**What would you do differently if you started over?**
Give myself more time and finish early instead of compressing
everything near the deadline — most of my mistakes came from rushing.
And I'd build one small habit: after every edit, run `git status` and
`git diff` to confirm the work actually exists on disk before assuming
it's done, and after every submission, open my own submitted link in
an incognito browser to confirm a grader could find everything from
that URL alone.

**What are you most proud of?**
Completing the full contribution cycle end to end — reproducing a real
issue, planning the fix, getting it through the project's linting and
type-checking standards, proving it against `main`, and submitting PR
#902 with a clean trail — and actually learning every concept along
the way instead of just getting it done.