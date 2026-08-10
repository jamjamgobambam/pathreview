## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output ([#50](https://github.com/ascherj/pathreview/issues/50))

### Understand
The repo analysis output (`GitHubTool.execute()` in `agent/tools/github_tool.py`) has no signal for whether a repository contains tests. Expected behavior: the output metadata dict should include a `has_tests: bool` field, `True` if the repo contains a `tests/` or `test/` directory, a `pytest.ini` file, or files matching `test_*.py` anywhere in the tree. Actual behavior, confirmed locally: the field doesn't exist at all. I wrote a reproduction test (`tests/unit/test_github_tool.py`, commit `98887e14dd3ee6ac5c5f41359c88305333593d1c`) that asserts `result.data.get("has_tests") is True` for a repo with a `tests/` dir — it fails today with `AssertionError: assert None is True`, since no `_has_tests()` method exists, unlike the sibling `_has_readme()` method that already handles a similar existence check.

### Map
- `agent/tools/github_tool.py` — add a new `_has_tests()` method to `GitHubTool`, and call it from `_fetch_repo_metadata()` alongside the existing `_has_readme()` call
- `tests/unit/test_github_tool.py` — extend beyond the single reproduction test with cases for each detection signal (tests/ dir, pytest.ini, test_*.py) and the negative case
- No changes expected in `agent/orchestrator.py` — `has_tests` will just pass through the existing `tool_results` dict unchanged; only touch if implementation reveals otherwise

### Plan
1. Decide the GitHub API call for detecting test presence. `_has_readme()` uses a single `HEAD /repos/{u}/{r}/readme` request, but tests can live anywhere in the tree, so a single-directory Contents API call (`GET /repos/{u}/{r}/contents/`) won't catch nested `test_*.py` files. Likely need the Git Trees API (`GET /repos/{u}/{r}/git/trees/{default_branch}?recursive=1`) to get the full file list in one call.
2. Implement `_has_tests(username, repo_name)` on `GitHubTool`, mirroring `_has_readme()`'s structure and error handling (return `False` on any request failure rather than raising).
3. Wire the new field into `_fetch_repo_metadata()`'s returned `metadata` dict, next to `has_readme`.
4. Extend `tests/unit/test_github_tool.py` with cases: `tests/` directory present, `test_*.py` files present with no `tests/` dir, neither present (expect `False`), and an API-error case.
5. Run the full test file and confirm the Week 8 reproduction test now passes.

### Inputs & outputs
- **Input:** unchanged — `{"github_username": str, "repo_name": str}`
- **Output:** the existing metadata dict, now including `"has_tests": bool`

### Risks & unknowns
- Need the repo's default branch name before calling the recursive tree API — the existing repo metadata response already includes `default_branch`, so I'll need to capture that value in `_fetch_repo_metadata()` rather than adding a separate lookup call.
- The recursive tree API can be truncated for very large repos (response includes `"truncated": true`) — undecided whether to handle this explicitly or accept it as a known limitation for v1.
- Unauthenticated GitHub API requests are capped at 60/hour; this adds a second call on top of the existing metadata + readme calls, so rate limiting is more likely to bite during grading/demo.
- Issue text doesn't specify whether nested test directories (e.g. `backend/tests/`) should count, or only top-level — assuming yes (any depth) since that matches how the recursive tree API naturally works, but calling this out as an assumption.

### Edge cases
- Repo has no tests anywhere → `has_tests: False`
- Repo API call fails or 404s → should degrade gracefully to `False`, same as `_has_readme()` does today, not raise
- Empty repository (no commits yet) → the tree API can return a 409 Conflict; needs a fallback to `False`
- Case sensitivity of directory/file names (`Tests/` vs `tests/`)
- Private repo accessed without an API token → same 403/404 handling already present in `execute()`'s exception handling should cover this, but worth a explicit test case
