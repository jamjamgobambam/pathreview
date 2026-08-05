## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50



**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The repo analysis pipeline is supposed to report whether a scanned repository
has tests, but the detection is currently broken. The logic for this already
exists in `ingestion/parsers/repo_analyzer.py` (`_detect_tests`), and looks
for common test indicators like a `tests/` directory or `pytest.ini`.
However, this logic depends on a `file_structure` field in the repo data that
is never actually populated anywhere in the codebase — `github_tool.py`,
which fetches repo metadata from the GitHub API, never includes a file
listing. As a result, `has_tests` always evaluates to `False` regardless of
the real repository contents. A correct fix will likely involve fetching the
repo's file tree in `github_tool.py` and
passing it through as `file_structure` so the existing detection logic in
`repo_analyzer.py` has real data to work with.

**Selection notes:**
I chose this issue as a Tier 1/good-first-issue because I'm working in this
codebase for the first time and wanted something with a small, well-defined
surface area. The issue names exactly two relevant files, which matched what
I found once I explored the repo (one of the two had actually moved locations,
which I confirmed before starting). The scope — adding/wiring up a single
boolean field — felt appropriately sized for a first contribution, even though
my investigation revealed the actual fix needs to happen upstream of where the
issue originally pointed.

**Branch name:** feat/50-has-tests-detection

**Setup confirmation:** [x] App runs locally at localhost:5173


**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Kshukla10/pathreview/commit/9fc5a9180a1d921bb5aef89e829ce6e832b2e8cd

**Reproduction summary:**
I fetched real GitHub repo data and ran it through the test-detection code.
It never receives a file list in the first place, so it always says "no
tests" even when tests exist — I wrote two committed pytest tests proving
this in tests/unit/test_repo_analyzer.py.

**PLAN.md link:** https://github.com/Kshukla10/pathreview/blob/feat/50-has-tests-detection/PLAN.md

**Blockers or open questions:**
Need to confirm whether we're using an authenticated GitHub connection to
avoid rate limits, and whether file_structure should be a flat string or a
list — leaning toward string based on how the existing detection code uses it.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in agent/tools/github_tool.py — added a
_fetch_file_structure method that calls GitHub's Git Trees API and wires
it into the metadata dict returned by _fetch_repo_metadata. Verified
locally that has_tests now correctly returns True for a real repo with
tests (previously always False, since the file_structure field it depends
on was never populated). Added 4 new unit tests in
tests/unit/test_github_tool.py covering the success case, API failure
handling, truncated tree handling, and metadata wiring. Fixed a
pre-existing mypy no-any-return error in _has_readme while in the area.
Confirmed via baseline comparison against main (57 failed/375 passed there
vs. 53 failed/381 passed on this branch) that my changes introduce no new
test failures — all pre-existing failures are in unrelated modules.

**Next steps:**
Opened a draft PR (#598), the fix is fully tested and self-reviewed
against CONTRIBUTING.md standards.

**Blockers:**
None currently.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/598

**Branch:** feat/50-has-tests-detection

**What you built:**
Fixed has_tests detection by adding a _fetch_file_structure method to
GitHubTool that calls GitHub's Git Trees API and populates the previously
missing file_structure field, which the existing detection logic in
repo_analyzer.py depends on. Also fixes has_ci and tech_stack, which
depended on the same field.

**Tests added or updated:**
tests/unit/test_github_tool.py — 4 new tests covering the success case,
API failure handling, truncated tree handling, and metadata wiring.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (no new failures vs. baseline: 53 vs. 57 pre-existing)

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No

**Summary of feedback:**
I worked through the issue selection, reproduction,
and implementation close to the deadline, which didn't leave enough time to
share my draft PR in Slack and get peer feedback before finalizing. That's
a timing tradeoff I'd fix if I started over — noted in the reflection below.

**How you responded:**
N/A 

### Reflection

**What was harder than you expected?**
The issue itself described a fix in the wrong file. `_detect_tests` in
repo_analyzer.py was already implemented correctly — the issue's suggested
location (agent/tools/repo_analyzer.py) didn't even exist anymore, and the
real bug was one layer upstream, in github_tool.py never populating the
file_structure field the detection logic depended on. I expected issue
descriptions to be a reliable map of what to change; instead, verifying the
premise of the issue against the actual code was itself most of the work.
I also underestimated how much of my time would go to environment setup
(Docker, WSL, Git Bash vs. PowerShell, make not being installed) before I
wrote a single line of the actual fix.

**What did you learn about working in a large codebase?**
I learned to trace data through a pipeline rather than trust a single
file in isolation — the bug only became visible once I followed
repo_data from where GitHubTool builds it through to where
RepoAnalyzer.parse() consumes it. I also learned that existing test files
(like test_readme_parser.py) are a better guide to a codebase's conventions
than any style guide, since they show real patterns for fixtures, mocking,
and naming that I matched rather than guessed at.

**How did AI tools help — and where did they fall short?**
AI was most useful for quickly diagnosing tool errors (mypy/ruff/black
failures, Docker/WSL setup issues) and for drafting boilerplate like test
scaffolding once I'd already found the real bug. It fell short at the
actual investigation — finding that file_structure was never populated
required me to actually read both files side by side and reason about the
data flow; that step needed my own attention on the specific codebase, not
something I could shortcut.

**What would you do differently if you started over?**
I'd start earlier in the week rather than compressing issue selection,
reproduction, and implementation close to the deadline — that timing
crunch meant I didn't leave room to share my draft PR for peer feedback
before finalizing, which the process explicitly recommends doing early.
I'd also verify the issue's premise against the actual code before writing
my Week 7 problem summary, rather than assuming the issue's suggested file
paths were still accurate. And I'd set up my dev environment (Docker, make,
correct shell) before selecting an issue, since that friction ate into time
I could've spent on the actual investigation.

**What are you most proud of from this module?**
Finding that the bug wasn't where the issue said it was. The issue pointed
at repo_analyzer.py, but the real problem was one layer upstream in
github_tool.py, which never populated the file_structure field the
detection logic depended on. Fixing that also silently fixed has_ci and
tech_stack, which depended on the same missing data — that felt like real
debugging, not just following instructions from the issue description.