## Solution plan

**Issue:** Add a mock GitHub API server for integration tests — https://github.com/ascherj/pathreview/issues/57

### Understand

The root cause is that `GitHubTool` (`agent/tools/github_tool.py`) hardcodes `self.base_url = "https://api.github.com"`, so any integration test that exercises it has no choice but to call the real GitHub API. Expected behavior: GitHub tool integration tests run deterministically in CI, independent of network access or GitHub's rate limits, and exercise the same success/error paths `GitHubTool.execute()` already handles. Actual behavior today: there is no way to test the tool except by hitting the live API (confirmed in the Week 8 reproduction — the test passes with network access and fails outright with it off), which is why these tests are skipped rather than run in CI.

### Map

- `agent/tools/github_tool.py` — needs `base_url` to become configurable (constructor param, defaulting to the real API) so tests can point it at a local mock server.
- `tests/integration/test_github_tool.py` — currently holds only the throwaway reproduction test; will be rewritten to use a `pytest-httpserver` fixture instead of the live API.
- `tests/fixtures/github_responses/` — doesn't exist yet; will hold JSON fixture files for each response shape the mock server serves.
- `tests/conftest.py` — likely home for a shared `httpserver`-based fixture that constructs a `GitHubTool` pointed at the mock, so it isn't duplicated per test.
- `pyproject.toml` — no changes needed; `pytest-httpserver` is already a dev dependency.

### Plan

1. Add a `base_url` constructor parameter to `GitHubTool.__init__`, defaulting to `"https://api.github.com"`, so existing callers are unaffected but tests can override it.
2. Create `tests/fixtures/github_responses/` with JSON fixtures covering: a successful repo response, a successful readme HEAD (200), a 404 repo-not-found response, and a 403 rate-limit response.
3. Add a pytest fixture (in `tests/conftest.py` or locally in the test file) that spins up `pytest_httpserver.HTTPServer`, registers handlers for `/repos/{username}/{repo}` and `/repos/{username}/{repo}/readme` serving the fixtures above, and constructs a `GitHubTool` with `base_url` pointed at it.
4. Rewrite `tests/integration/test_github_tool.py` to remove the live-API reproduction test and add cases for: successful metadata fetch, repo not found (404), rate limited (403), and malformed JSON — asserting `GitHubTool.execute()`'s existing error handling behaves correctly for each.
5. Run `make check && make test-unit` plus the new integration tests locally, and confirm they pass in CI without needing a `GITHUB_TOKEN`.

### Inputs & outputs

Input: an optional `base_url` argument to `GitHubTool` (new), plus the existing `github_username`/`repo_name` input to `execute()`. Output: no change to `GitHubTool`'s public behavior or `ToolResult` shape — only the tests change, plus the new fixture files and mock-server wiring. The observable change is that `tests/integration/test_github_tool.py` runs reliably in CI with no network dependency.

### Risks & unknowns

- Need to make sure `pytest_httpserver`'s handler registration matches the exact path/method combinations `GitHubTool` calls (`GET` for repo metadata, `HEAD` for readme check) — a mismatch would silently 404 against the mock instead of the real API's 404.
- Should double check whether `_has_readme`'s broad `except Exception: return False` could mask a misconfigured mock server (e.g., connection refused would also just return `False`, same as a real "no readme" case) — worth a test that explicitly checks the true-README-exists path so this isn't masked.
- Still unsure whether to put the `httpserver` fixture in `tests/conftest.py` (shared) or locally in the test module — leaning shared since other future tools reading from GitHub could reuse it later, but keeping scope to this issue for now.

### Edge cases

- Successful metadata fetch with a repo that has a README.
- Successful metadata fetch with a repo that has no README (`_has_readme` returns `False`).
- 404 — repository not found.
- 403 — rate limited or access denied.
- Malformed/non-JSON response body — should surface as a generic error rather than an unhandled exception, per the existing `except Exception` branch in `execute()`.
