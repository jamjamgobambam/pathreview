## Solution plan

**Issue #57:** Add a mock GitHub API server for integration tests (https://github.com/ascherj/pathreview/issues/57)

### Understand
<!--
What is the root cause of this issue? What behavior is expected vs. actual?
-->
The current codebase skip Github tool tests because they require live Github access. The goal is creating a mock Github server that answers with pre-saved fake data in order to run Github tool tests without sending requests to Github.

- Actual bahavior: GitHub tool behavior is unverified as tests are skipped
- Expected behavior: Tests for GitHub tool run on a local mock server and confirm that the Github tool functions properly

### Map
<!--
Which files, functions, or modules are involved?
List the specific files you expect to touch.
-->
Existing modules involved: 
- `agent\tools\github_tool.py`
    - `_fetch_repo_metadata` → `GET {base_url}/repos/{user}/{repo}`
    - `_has_readme` → `HEAD {base_url}/repos/{user}/{repo}/readme`
    - `execute` → maps errors
        - 404 Not Found: "Repository not found"
        - 403 Forbidden: "Rate limited or access denied"

Files to create:
- `tests/integration/test_github_tool.py` - GitHub tool tests
- `tests/fixtures/github_responses/` - pre-save fixtures

Dependency:
- `pytest-httpserver` (already a dependency)

### Plan
<!--
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
-->
1. First write out the fixtures based on the implementation of GitHub tool that covers the following
    - note that `repo_json = response.json()` for GitHub metadata, so a full success response should be in the json format (`repo_success.json`)
    - a response with some nulls to test out how the nulls are being handled when extract metadata (lines 98-110 in `github_tool.py`)
    - a response with `status_code` as `404`, `403`, and another generic error for fetching metadata. See if error messages for the`HTTPStatusError`exception are correct
    - a HEAD handler retruning `200` when README is present
    - a HEAD handler r
2. Set up the mock server and write out the names for the tests needed without implementing them
    - need to inject `tool.base_url = httpserver.url_for("")`
3. Implement the tests the cover:
    - success path (using fixture)
    - null-fallbacks (using fixture)
    - README absence
    - error messages (using fixture)
    - missing input

### Inputs & outputs
<!--
What does your fix take as input? What should it produce or change?
-->
Input:
- Tool input: `{"github_username", "repo_name"}`
- Injected `tool.base_url` pointing at the local mock server

Output:
- New files only: `tests/integration/test_github_tool.py` + fixtures in `tests/fixtures/github_responses/`
- No production code change (base_url injected in the test)
- GitHub tool tests run offline in CI without live GitHub access

### Risks & unknowns
<!--
What could go wrong? What are you still unsure about?
-->
- For `_has_readme`, ` except Exception: return False` so all exceptions are covered. The tests might silently pass if no `HEAD` handler
- Fixture JSON must use real GitHub field names (stargazers_count, forks_count, pushed_at, topics, homepage) for .get() extraction. This would have to assume to be true, and the test meeds to follow the naming strictly.


### Edge cases
<!--
What inputs or states should your fix handle gracefully?
-->
- Null `description` / `language` / `homepage` → fallbacks (`""`, `"Unknown"`)
- Missing `topics` / `homepage` keys → defaults
- 404 (repo not found), 403 (rate limited), other/generic status → mapped error messages
- README present (`HEAD` 200) vs. absent 
- Missing `github_username` or `repo_name` → `success=False`, no server call