## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output — #50
(https://github.com/ascherj/pathreview/issues/50) · issue-catalog id **C-10**
· Tier 1 · labels: `agent`, `tests`, `enhancement`, `good first issue`

### Understand

**Root cause.** The agent-side repository analysis tool,
`GitHubTool._fetch_repo_metadata()` in `agent/tools/github_tool.py`, builds the
metadata dict that represents a repo's "analysis output" (lines 99-110). That
dict already surfaces `has_readme` (via the `_has_readme` helper) but has **no
`has_tests` field**. Test coverage is a strong portfolio signal, so the agent's
analysis should report whether a repo ships tests.

**Expected vs. actual.**
- *Actual:* The analysis output contains `name`, `description`,
  `primary_language`, `star_count`, `fork_count`, `open_issues_count`,
  `last_commit_date`, `has_readme`, `topics`, `homepage`. No test signal.
- *Expected:* The same output additionally contains `has_tests: bool`, set
  `True` when the repo has a `tests/` or `test/` directory, a `pytest.ini`, or
  files matching `test_*.py` — mirroring the acceptance criteria in the issue.

**Note on scope (verified during reproduction).** There are two repo analyzers
in the codebase. `ingestion/parsers/repo_analyzer.py` *already* implements
`has_tests` (its `_detect_tests` helper) — that is a separate ingestion path
and is out of scope. The issue names `agent/tools/github_tool.py` and
`agent/tools/repo_analyzer.py`; the latter does **not exist** in the current
tree, so the real, addressable gap is `GitHubTool`. This fix is scoped to the
agent tool the issue targets and that is genuinely missing the field.

### Map

Files I expect to touch:

- **`agent/tools/github_tool.py`** — add a `has_tests` key to the metadata dict
  in `_fetch_repo_metadata()` (lines 99-110) and add a new `_has_tests(username,
  repo_name)` helper modeled on the existing `_has_readme()` (lines 117-137).
- **`tests/unit/test_github_tool.py`** — the reproduction test already added in
  this branch; extend it with cases that assert `has_tests` is `True`/`False`
  for repos that do / don't contain test markers (mocking the GitHub API).

Reference (read, not edited):
- `agent/tools/base.py` — `BaseTool` / `ToolResult` container.
- `agent/tools/github_tool.py:117` — `_has_readme`, the template for `_has_tests`.
- `ingestion/parsers/repo_analyzer.py:121` — existing `_detect_tests` logic to
  reuse the same detection markers (`tests/`, `test/`, `pytest.ini`, `test_`).
- `tests/unit/test_readme_scorer.py` / `test_tech_detector.py` — test patterns.

### Plan

1. **Add detection helper.** Implement `_has_tests(username, repo_name) -> bool`
   in `GitHubTool`. Fetch the repo's file tree via the GitHub Git Trees API
   (`GET /repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1`) and return
   `True` if any path matches a test marker: a `tests/` or `test/` directory, a
   `pytest.ini`, or a file matching `test_*.py`. Reuse the auth-header pattern
   from `_has_readme`.
2. **Wire it into the output.** Add `"has_tests": self._has_tests(username,
   repo_name)` to the metadata dict in `_fetch_repo_metadata()`.
3. **Handle failure gracefully.** Wrap the tree call in try/except and default to
   `False` on any error (missing branch, truncated tree, network/rate-limit
   failure) so analysis never crashes — same defensive shape as `_has_readme`.
4. **Extend tests.** Turn the reproduction test green and add cases: repo with a
   `tests/` dir → `True`; repo with only `test_foo.py` → `True`; repo with no
   test markers → `False`; API error → `False`.
5. **Verify.** Run `pytest tests/unit/test_github_tool.py`, then the full
   `make test` / lint, and confirm no regression to `has_readme` or other fields.

### Inputs & outputs

- **Input:** `github_username` and `repo_name` (already the tool's input), plus
  the repo's file tree fetched from the GitHub API.
- **Output:** the existing analysis dict gains one key, `has_tests: bool`. No
  existing field changes; no schema/DB migration required (the output is an
  untyped dict flowing through the agent orchestrator, not a Pydantic response
  model).

### Risks & unknowns

- **Extra API call / rate limits.** Detecting tests needs the file tree, i.e. an
  additional GitHub request per repo (like `_has_readme`). Under unauthenticated
  rate limits this adds pressure; acceptable for Tier 1 but worth noting.
- **Truncated trees.** The Git Trees API truncates very large repos (`truncated:
  true`). In that case detection may under-report; I'll default to `False` and
  leave a comment rather than paginating (out of scope for Tier 1).
- **Default branch.** Need `default_branch` from the repo JSON; not every code
  path guarantees it — fall back to `"main"` then `"master"` if absent.
- **Unknown:** whether any downstream consumer (orchestrator / review prompt)
  should also *use* `has_tests`. The issue only asks to surface it, so I'll stop
  at the tool output unless review confirms otherwise.

### Edge cases

- Repo with `tests/` **or** `test/` directory → `True`.
- Repo with `pytest.ini` at root but no test dir → `True`.
- Repo with scattered `test_*.py` files but no `tests/` dir → `True`.
- Repo with a `contest/` or `latest/` path (false-positive traps) → must **not**
  match on a naive `"test" in path` substring; match on path segments/filenames.
- Empty repo / no tree / private-or-404 / rate-limited → `False`, no exception.
- Non-Python repos (JS `__tests__/`, `spec/`) → out of scope for the stated
  criteria, but the marker list is easy to extend later.
