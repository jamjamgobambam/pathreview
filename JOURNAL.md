## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Test coverage detection logic

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PathReview analyzer currently does not detect whether a repository contains tests. This issue requires adding logic to identify test directories (tests/ or test/), pytest.ini, or files matching test_*.py. The goal is to surface a boolean field `has_tests` in the analysis output. This affects the repo analyzer and GitHub tool modules.

**Branch name:** feat/50-test-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Alessandra005/pathreview/commit/3cfb305

**Reproduction summary:**
Created a mocked unit test (`tests/unit/test_github_tool.py`) that runs `GitHubTool.execute()` and checks that `"has_tests"` appears in the returned metadata. The test fails, showing that the field is completely missing even though the sample repo includes a `tests/` directory. The test uses mocked `httpx.get` and `httpx.head` calls so it stays offline and avoids GitHub rate limits, following the same mocking style already used in other tests under `tests/unit/`.

**PLAN.md link:** https://github.com/Alessandra005/pathreview/blob/feat/50-test-detection/PLAN.md

**Blockers or open questions:**
The original issue pointed to `agent/tools/repo_analyzer.py`, but that file doesn’t exist in this project. The correct place for the fix is `GitHubTool._fetch_repo_metadata`, next to where `has_readme` is already computed. While writing the test, a separate mypy error surfaced in the `_has_readme` helper. This issue isn’t related to #50, so I’m not fixing it here, but I’m noting it in the plan for future cleanup.

## Week 9 — Solution building & PR submission

### Check-in 1

**Current progress:**
Implemented the fix in `GitHubTool`. Added a `_has_tests(username, repo_name)` helper (modeled on `_has_readme`) that lists the repo root via the GitHub contents API and detects a `tests/` or `test/` directory, a `pytest.ini` file, or a root-level `test_*.py` file, then wired its result into `_fetch_repo_metadata` as a new `has_tests` boolean. The Week 8 reproduction test now passes. Sub-tasks 1–3 from PLAN.md are done.

**Next steps:**
Expand `tests/unit/test_github_tool.py` from the single reproduction test into a full suite covering every detection branch and the graceful-failure paths (non-200, non-list payload, network error). Run `make check` and `make test-unit`, confirm my changes add no new failures on top of the codebase's documented pre-existing ones, then open a draft PR for peer feedback.

**Blockers:**
The codebase has a large number of pre-existing `make check`/`make test-unit` failures unrelated to #50. I recorded a baseline (54 failing unit tests, 182 ruff errors, 5 mypy errors) before starting so I can prove my change doesn't make things worse.

---

### Check-in 2 

**PR link:** https://github.com/ascherj/pathreview/pull/644

**Branch:** `feat/50-test-detection`

**What you built:**
A `has_tests` boolean was added to the GitHub repo analysis output. `GitHubTool._has_tests` queries the GitHub contents API for the repository root and returns `True` when it finds a `tests/`/`test/` directory, a `pytest.ini`, or a root-level `test_*.py` file, mirroring the existing `has_readme` signal. It returns explicit booleans and swallows non-200/malformed/network errors as `False`, so it adds no new failure mode to metadata fetching.

**Tests added or updated:**
`tests/unit/test_github_tool.py` — replaced the single reproduction test with 10 unit tests: each detection branch (`tests/`, `test/`, `pytest.ini`, `test_*.py`), the no-indicator case, a negative case for non-test files that merely contain "test", the non-200 / non-list / exception fallbacks, and an end-to-end check that `execute()` surfaces `has_tests` as a boolean. All 10 pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_"Passes" = no new failures vs. the documented pre-existing ones. Baseline → after: unit tests 54 → 53 failing, ruff 182 → 181, mypy 5 → 5. My two files pass ruff, black, and mypy clean._

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] N/A

**Summary of feedback:**
Reviewer feedback isn't part of the Summer 2026 offering per the course note.

**How you responded:**
N/A.

---

### Reflection

**What was harder than you expected?**
The setup took more time than the fix. PowerShell broke the `pip install httpx>=0.29.0` command and made a random `=0.29.0` file. `pytest` kept running from a global Python instead of my venv. Then `pip install -e .` didn’t install `pytest` because it’s under the `[dev]` extras, so I had to use `pip install -e ".[dev]"`. I also spent part of Week 8 on the wrong branch and had to check both logs before deleting the stale one.

**What did you learn about working in a large codebase?**
The issue's own file list was wrong. It named `agent/tools/repo_analyzer.py` as one of two relevant files, and that file simply doesn't exist in this codebase. I had to trace `agent/orchestrator.py` to understand that there's no separate "analysis" layer at all; each tool just returns its own dict, and `GitHubTool`'s metadata dict is the real "repo analysis output" the issue meant. I only found the right place to add `has_tests` by grepping for how the existing `has_readme` field was implemented and matching that pattern exactly. 

**How did AI tools help — and where did they fall short?**
AI was most useful for the archaeology, pointing me at `orchestrator.py` when the issue's file reference turned out to be stale, catching that `_has_readme` used `httpx.head` while the main metadata fetch used `httpx.get`, and matching this codebase's existing test conventions instead of me guessing at a style from scratch. It also caught concrete mistakes fast such as an unclosed code fence in my PLAN.md that would've broken rendering. It fell short sometimes because it can help explain an error, but it can’t prevent the real-world setup problems. All the messy parts like PowerShell breaking the command, missing dev deps, being on the wrong branch, and mypy only failing once a test touched the module, I still had to catch by actually running things myself. It really couldn’t see any of this without me testing it on my own machine first.

**What would you do differently if you started over?**
I’d check the `[dev]` optional deps on day one and install everything with `pip install -e ".[dev]"` instead of wasting time wondering why `pytest` wasn’t there. I’d also double‑check my active branch before doing any work so I don’t repeat the Week 8 mistake of landing commits on `issue-50` instead of `feat/50-test-detection`. And I’d plan time upfront to verify the issue against the actual codebase, since the stale `repo_analyzer.py` reference cost more time than it should have.

**What are you most proud of from this module?**
Catching that the issue's stated file (`repo_analyzer.py`) didn't actually exist, instead of assuming the issue description was accurate and trying to force my fix into a file I'd have had to invent from scratch. Going and verifying the real structure of the codebase before writing PLAN.md, and documenting that discovery instead of quietly working around it. It felt like the most honest.
