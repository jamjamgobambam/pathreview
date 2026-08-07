## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output (#50)](https://github.com/ascherj/pathreview/issues/50)

### Understand

**Root cause.** The agent's GitHub tool assembles repository metadata in
`GitHubTool._fetch_repo_metadata` ([agent/tools/github_tool.py:99](agent/tools/github_tool.py)).
It reports fields such as `primary_language`, `star_count`, and `has_readme`,
but it never inspects the repository for a test suite, so there is no
`has_tests` signal anywhere in the analysis output. This is a **feature gap**,
not a crash — the tool works, it just omits a field.

- **Expected:** `execute(...).data` includes a `has_tests: bool` that is `True`
  when the repo has a `tests/` or `test/` directory, a `pytest.ini`, or any
  file matching `test_*.py`, and `False` otherwise.
- **Actual:** the output dict has no `has_tests` key at all (see the reproduction
  test, which asserts the key exists and currently fails with
  `AssertionError: analysis output is missing the has_tests field`).

The existing `has_readme` / `_has_readme` pair is the design template to mirror:
a boolean field in the metadata dict, backed by a small private helper that
queries the GitHub API.

### Map

Files I expect to touch:

- **`agent/tools/github_tool.py`** — primary change.
  - `_fetch_repo_metadata` (line ~99): capture `default_branch` from the repo
    JSON and add `"has_tests": self._has_tests(...)` to the metadata dict.
  - New `_has_tests(self, username, repo_name, default_branch) -> bool` helper,
    modeled on `_has_readme` (lines 117–137), including the same auth-header
    handling and defensive `try/except -> False`.
  - Fix `_has_readme`'s return type while I'm here: `return response.status_code
    == 200` currently returns `Any` (mypy `no-any-return` at line 135); wrap in
    `bool(...)`. Needed so the pre-commit mypy hook passes.
- **`tests/unit/test_github_tool.py`** — expand the reproduction test into full
  coverage: field present, `True` when tests exist, `False` when they don't,
  and graceful `False` on API failure / truncated tree.

Files I do **not** expect to change: `skill_extractor.py`, `orchestrator.py`,
etc. consume `repo_metadata` via `.get()` with defaults, so a new key is purely
additive. (The issue also lists `agent/tools/repo_analyzer.py`, which does not
exist in the repo — the metadata is built in `github_tool.py`.)

### Plan

1. **Detection helper.** Add `_has_tests`. Fetch the repo's file tree in one call
   via the Git Trees API
   (`GET /repos/{user}/{repo}/git/trees/{default_branch}?recursive=1`), then
   check the returned paths locally for: a top-level or nested `tests/`/`test/`
   directory, a `pytest.ini`, or any path whose basename matches `test_*.py`.
2. **Wire it into the output.** Read `default_branch` in `_fetch_repo_metadata`
   (default `"main"`), call `_has_tests`, and add `has_tests` to the metadata
   dict next to `has_readme`. Add it to the existing `logger.info` line too.
3. **Fix the `_has_readme` return-type nit** so mypy passes and the new helper
   follows a clean, typed pattern.
4. **Tests.** Grow `tests/unit/test_github_tool.py` to cover positive detection
   (each of the three signals), negative detection, and failure fallback, all
   with mocked httpx — no network.
5. **Verify.** `make test-unit`, then `make check` (ruff + black + mypy) so the
   pre-commit hook passes without `--no-verify`. Open the PR against `upstream`.

### Inputs & outputs

- **Input:** the same `execute` input as today — `{"github_username": str,
  "repo_name": str}` — plus, internally, the repo's `default_branch` and the
  recursive tree of file paths from the GitHub API.
- **Output:** the returned `ToolResult.data` dict gains one key,
  `"has_tests": bool`. No existing field changes. No change to `execute`'s
  signature or to `ToolResult`.

### Risks & unknowns

- **Extra API call = rate limits.** `_has_tests` adds another request per repo
  (on top of `_fetch_repo_metadata` and `_has_readme`). Unauthenticated GitHub
  is 60 req/hr; this could exhaust it faster. Mitigation: reuse the `api_token`
  header already supported, and make failures degrade to `False` rather than
  raising (matching `_has_readme`).
- **Truncated trees.** The Git Trees API sets `"truncated": true` for very large
  repos and omits entries. A test file could be missed → false `False`. Need to
  decide: accept the limitation, or fall back to top-level Contents API checks
  for `tests/`, `test/`, `pytest.ini` when truncated. Leaning toward the
  fallback for the common signals.
- **Default branch.** Not every repo uses `main`; I must read `default_branch`
  from the repo JSON rather than hardcoding, or the tree fetch 404s.
- **Non-Python tests.** The issue scopes detection to Python conventions
  (`test_*.py`, `pytest.ini`). JS/other test layouts are out of scope for this
  issue — worth noting in the PR so reviewers know it's intentional.

### Edge cases the fix should handle gracefully

- Repo with **no tests at all** → `has_tests: False` (not missing, not an error).
- **`tests/` vs `test/`** and **nested** test dirs (e.g. `src/pkg/tests/`).
- **`pytest.ini` present but no `tests/` dir** → still `True`.
- **`test_foo.py` at any depth** matched; a file merely *named* `contest.py` or a
  `latest_*.py` file **not** falsely matched.
- **GitHub API errors** (404 private/missing repo, 403 rate limit, network
  timeout) → helper returns `False` and the overall tool still succeeds, exactly
  like `_has_readme`.
- **Empty repository** (no default branch / empty tree) → `has_tests: False`.
