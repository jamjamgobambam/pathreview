## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output
(https://github.com/jamjamgobambam/pathreview/issues/50)

### Understand
The root cause is that `_fetch_repo_metadata` in `agent/tools/github_tool.py` never
computes or adds a `has_tests` key. It builds a metadata dict that includes `has_readme`
(worked out by the `_has_readme` helper) but stops there. Expected behavior is that the
tool output also reports whether the repository ships automated tests. Actual behavior is
that consumers of this tool get no test signal at all. The parallel module
`ingestion/parsers/repo_analyzer.py` already detects tests through its `_detect_tests`
method, so the agent GitHub tool is inconsistent with the rest of the codebase.

### Map
Files and functions involved:
- `agent/tools/github_tool.py`: add a `_has_tests` helper and insert a `has_tests` key
  into the metadata dict in `_fetch_repo_metadata` (right after `has_readme` on line 107).
  The existing `_has_readme` helper (line 117) is the shape to mirror.
- `tests/unit/test_github_tool.py`: new file, expand the Week 8 reproduction test into
  full coverage of the new behavior.
- Reference only, not edited: `ingestion/parsers/repo_analyzer.py` `_detect_tests` (lines
  121 to 131) supplies the detection vocabulary (`tests/`, `test/`, `pytest.ini`,
  `spec/`, `__tests__`).

Note: the issue manifest listed `agent/tools/repo_analyzer.py`, but that path does not
exist. The real analyzer lives under `ingestion/parsers/`, so the only production file I
touch is `agent/tools/github_tool.py`.

### Plan
1. Add a `_has_tests(self, username, repo_name)` helper that queries the GitHub contents
   listing for the repository root and checks the entry names against the same test
   indicators the analyzer uses.
2. Insert `"has_tests": self._has_tests(username, repo_name)` into the metadata dict in
   `_fetch_repo_metadata`, directly after the `has_readme` entry, so the output shape
   stays predictable.
3. Wrap the network call in a try and except that returns `False` on any failure, exactly
   the way `_has_readme` already guards itself, so a missing or private repo never raises.
4. Type the new helper fully (`-> bool`, typed args) so `make typecheck` (mypy with
   `disallow_untyped_defs`) stays green.
5. Expand `tests/unit/test_github_tool.py` to cover the true case, the false case, and the
   network error case, all with mocked httpx.

### Inputs & outputs
Input is unchanged: `execute` still takes `{"github_username": str, "repo_name": str}`.
Output changes: `ToolResult.data` gains one new key, `has_tests` (bool). The new private
helper signature is `_has_tests(self, username: str, repo_name: str) -> bool`. The fix
adds one extra GitHub API call per repository (the contents listing), alongside the
existing readme check.

### Risks & unknowns
- GitHub has no single tests endpoint the way it has `/readme`, so `_has_tests` must read
  the root contents listing in `agent/tools/github_tool.py`. A root only listing can miss
  test directories nested deeper in the tree or `test_*.py` files that live below the
  root. The recursive git trees API would catch those but is heavier and needs the default
  branch name, so I need to decide how deep to look.
- The extra call raises pressure on the unauthenticated GitHub rate limit (60 requests per
  hour), which `_has_readme` already contributes to.
- mypy runs with `disallow_untyped_defs = true` in `pyproject.toml`, so an untyped helper
  will fail `make typecheck`.
- Unknown: whether anything in `api/schemas/` expects a fixed key set from this tool. I
  need to grep for consumers of the metadata dict before assuming the new key is safe.

### Edge cases
- Repository with a `tests/` directory returns `has_tests` True.
- Repository with only a `pytest.ini` and no tests directory returns True.
- Repository with a `test_something.py` file at the root returns True.
- Repository with no test files or directories returns False.
- Repository that 404s or errors on the contents call returns False without raising, the
  same guard `_has_readme` uses.
- Empty repository whose contents endpoint returns nothing returns False.
