## Solution plan

**Issue:** [#57 — Add a mock GitHub API server for integration tests](https://github.com/ascherj/pathreview/issues/57)

### Understand
The `GitHubTool` in [agent/tools/github_tool.py](agent/tools/github_tool.py) fetches repository
metadata by calling the live GitHub REST API. Its `base_url` is hardcoded to `https://api.github.com` ([github_tool.py:23](agent/tools/github_tool.py#L23)), so any integration test that exercises the tool needs real network access, authentication, and is subject to GitHub's
rate limits. Because of that, the GitHub tool tests are skipped in CI — in fact `tests/integration/test_github_tool.py` and `tests/fixtures/github_responses/` do not exist yet, so the tool's request handling and error paths (200 success, 404 not found, 403 rate limit) are currently untested by automation.

- **Expected:** GitHub tool tests run deterministically and offline in CI against a local mock server.
- **Actual:** No tests exist; testing the tool would hit the real API, so it is left uncovered.

### Map
Files/functions involved:
- [agent/tools/github_tool.py](agent/tools/github_tool.py) — `GitHubTool.__init__` (make `base_url` injectable), `execute`, `_fetch_repo_metadata`, `_has_readme`. **Touch (small change).**
- `tests/integration/test_github_tool.py` — **create.** The test module.
- `tests/fixtures/github_responses/` — **create.** Canned JSON fixtures for GitHub endpoints.
- [tests/conftest.py](tests/conftest.py) — optionally add a fixture for the mock server / fixture loader.

No change needed to dependencies: `pytest-httpserver>=1.0.8` is already in the dev extras ([pyproject.toml:45](pyproject.toml#L45)), and CI installs `.[dev]` and runs `pytest tests/integration` ([.github/workflows/ci yml:77-79](.github/workflows/ci.yml#L77-L79)), so
a new test file is picked up automatically.

### Plan
1. **Make `base_url` injectable.** Add an optional `base_url` parameter to `GitHubTool.__init__` (defaulting to `https://api.github.com`) so tests can point the tool at the mock server.
2. **Add fixtures.** Create `tests/fixtures/github_responses/` with JSON files for a successful repo response and (if useful) a 404 body, mirroring the fields the tool reads (`name`, `description`, `language`, `stargazers_count`, `forks_count`, `open_issues_count`, `pushed_at`, `topics`, `homepage`).
3. **Write the test module.** In `tests/integration/test_github_tool.py`, use the `pytest-httpserver` `httpserver` fixture to register handlers for `/repos/{user}/{repo}` and `/repos/{user}/{repo}/readme`, construct the tool with `base_url=httpserver.url_for("")`, and assert the returned `ToolResult`. Mark tests with `@pytest.mark.integration` so `make test-integration` (`-m integration`) collects them.
4. **Cover the three paths:** success (200 → metadata mapped correctly, `has_readme` reflects the HEAD result), 404 → `success=False`, error `"Repository not found"`, and 403 → error `"Rate limited or access denied"`.
5. **Verify locally and in CI.** Run `make test-integration` (or `pytest tests/integration/test_github_tool.py -v`) and confirm it passes offline, then `make check` for lint/format/typecheck.

### Inputs & outputs
- **Input:** the tool's `execute()` takes `{"github_username": ..., "repo_name": ...}`; tests supply these plus a mock `base_url`.
- **Output/changes:** a new injectable `base_url` on `GitHubTool`, a new test module, and new JSON fixtures — enabling the GitHub tool tests to run in CI without live API access. No behavior change for production callers (default `base_url` is unchanged).

### Risks & unknowns
- `_has_readme` issues a separate `HEAD /repos/{user}/{repo}/readme` request; the mock server must register that route too or the success test will misreport `has_readme`.
- `pytest-httpserver` uses HTTP (not HTTPS); confirm `httpx` calls resolve to the mock URL correctly and no code re-prepends `https://`.
- Need to confirm whether the existing integration CI job (which spins up Postgres/Redis) imposes any extra setup on this test — the GitHub tool test itself needs neither.

### Edge cases
- Missing `github_username` or `repo_name` → tool returns `"Missing github_username or repo_name"` (no HTTP call). Worth a test.
- Null/absent JSON fields (e.g. `description`, `language`, `homepage`) → tool coalesces to `""` / `"Unknown"`; fixture should include at least one null to exercise this.
- README HEAD request failing/raising → `_has_readme` swallows the exception and returns `False`.
- Generic non-404/403 status (e.g. 500) → error string `"GitHub API error: 500"`.
