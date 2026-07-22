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
