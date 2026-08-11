## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output

**Tier:** [ ] Tier 1 

**Problem summary:**
The repo analyzer currently produces an analysis of a repository but doesn't report anything about test coverage, which is a signal recruiters and reviewers care about. This issue asks for a new has_tests boolean to be added to the analysis output, determined by checking for common test indicators — a tests/ or test/ directory, a pytest.ini file, or files matching the test_*.py naming pattern. The fix touches agent/tools/github_tool.py (likely where repo contents are fetched/listed) and agent/tools/repo_analyzer.py (where the analysis result is assembled), so the detection logic needs to plug into how the repo's file tree is already being read. A successful fix means any repo run through the analyzer returns has_tests: true or false accurately, without needing to clone the full repo if that can be avoided.

**Branch name:** feat/50-has-tests-detection

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aarohi-agrawal/pathreview/tree/feat/50-has-tests-detection/reproduce_has_tests_bug.py

**Reproduction summary:**
I found that `RepoAnalyzer._detect_tests()` already implements correct test-detection logic and already outputs `has_tests`, but `GitHubTool` never populates the `file_structure` field it depends on — so `has_tests` always evaluates to `False` in the real pipeline. I confirmed this by calling `RepoAnalyzer.parse()` directly with and without a `file_structure` key, showing the detection logic works correctly when given data but is never given real data today.

**PLAN.md link:** https://github.com/aarohi-agrawal/pathreview/tree/feat/50-has-tests-detection/PLAN.md


**Blockers or open questions:**
Need to confirm whether fixing `has_ci` (which has the same root-cause bug) is in scope for this issue or should be a separate PR — will ask in Slack/office hours before finalizing the Week 9 build.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented `_get_file_structure()` in `GitHubTool`, which fetches the repo's file tree via GitHub's Trees API and wires it into the metadata dict as `file_structure`. This is the field `RepoAnalyzer._detect_tests()` was already reading but never receiving, so `has_tests` (and `has_ci`) now reflect real repo contents instead of always returning `False`. Added `tests/unit/test_github_tool.py` with 3 tests covering the happy path, graceful fallback on API failure, and existing input-validation behavior. Confirmed via `make check` (181 errors, down from 182 baseline) and `make test-unit` (53 pre-existing failures unchanged, 3 new tests passing) that no regressions were introduced.

**Next steps:**
Manually verify against a couple of real GitHub repos, then open a draft PR and request feedback in Slack.

**Blockers:**
Still deciding whether fixing `has_ci` (same root cause) belongs in this PR or a separate one — will raise in Slack/office hours.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/778

**Branch:** feat/50-has-tests-detection

**What you built:**
Fixed `has_tests` (and `has_ci`) always returning `False` by having `GitHubTool` fetch the repo's file tree from GitHub's API and populate the `file_structure` field that `RepoAnalyzer._detect_tests()` was already reading but never receiving.

**Tests added or updated:**
Added `tests/unit/test_github_tool.py` with 3 tests covering the happy path (file_structure correctly populated and detected), graceful fallback on API failure, and existing input-validation behavior. Also manually verified against a real repo (`pytest-dev/pytest`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(181 pre-existing lint errors, down from 182 baseline, none new; 53 pre-existing test failures unchanged, plus 3 new tests passing — documented in the PR description)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments came in on the PR before this reflection was due. I shared the link but didn't get a chance to follow up in Slack for feedback before finalizing.

**How you responded:**
N/A — no feedback to respond to yet. If comments come in after submission, I'll address them in a follow-up commit and note it here.

---

### Reflection

**What was harder than you expected?**
Git itself was harder than the actual coding. Several times I thought I'd committed something and it turned out the commit had silently failed — usually because pre-commit hooks (ruff, black, mypy) rejected the commit, or because I hadn't actually staged the file with `git add` first. I also created my feature branch on GitHub directly, which meant my local clone didn't know about it until I ran `git fetch` and `git checkout` — something I hadn't run into before. The PR flow itself (comparing across forks, picking the right base/head repos and branches) also took a few tries to get right.

**What did you learn about working in a large codebase?**
The issue description didn't match what I actually found in the code. The issue asked me to "add" a `has_tests` boolean, but when I actually read `agent/tools/repo_analyzer.py`, the detection logic and the field already existed — the real bug was that `agent/tools/github_tool.py` never populated the `file_structure` field the detection logic depended on. I learned that understanding the *actual* root cause by reading the code carefully was more valuable than trusting the issue title at face value. I also learned how to separate pre-existing problems in a codebase (182 lint errors, 53 failing tests, none related to my change) from problems my own change introduced — and that "passes" in a real project means "doesn't make things worse," not "the whole codebase is clean."

**How did AI tools help — and where did they fall short?**
AI was most useful for pattern-matching: once I showed it an existing method like `_has_readme()`, it could draft `_get_file_structure()` in a consistent style, and it could translate cryptic mypy/ruff errors into plain explanations of what was actually wrong and why. It also helped me reason through git problems methodically (checking `git status`/`git log` before guessing) instead of panicking when a commit seemed to "disappear." Where it fell short: it couldn't see my actual terminal output, browser state, or repo contents unless I pasted them in, so I had to be the one who ran commands, checked file listings, and confirmed things worked — AI could guide the diagnosis but not observe the system directly. I also had to be the one to decide the real scope of the fix (whether `has_ci` belonged in this PR).

**What would you do differently if you started over?**
I'd read through the actual issue's referenced files (`github_tool.py` and `repo_analyzer.py`) *before* committing to the issue, not after — that would have surfaced the real root cause during issue selection instead of during Week 8's reproduction step. I'd also run `make check` and `make test-unit` to capture my baseline earlier, and I'd get in the habit of running `git status` after every commit attempt instead of assuming it worked.

**What are you most proud of from this module?**
Finding that the issue as written didn't match reality, and being able to explain precisely why — that `RepoAnalyzer` already had working detection logic, and the actual bug was one missing field upstream in `GitHubTool`. That took more careful reading than I expected going in, and it made the fix itself much more targeted than if I'd just "added a boolean" somewhere without understanding why it wasn't working.
