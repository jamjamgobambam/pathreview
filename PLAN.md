## Solution plan

**Issue:** [Add a has_tests boolean to the repo analysis output #50](https://github.com/ascherj/pathreview/issues/50)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

When the agent reviews a candidate's GitHub repo, nothing checks whether the project has automated tests. A well-tested repo and an untested one currently produce identical analysis output, so this engineering-maturity signal is silently dropped. Expected behavior: the analysis output includes a `has_tests` boolean derived from the repo's file tree (presence of a `tests/`/`test/` directory, a `pytest.ini`, or `test_*.py` files). Actual behavior: no such field exists, and no detection logic exists in `agent/tools/`.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `agent/tools/github_tool.py` — currently fetches repo metadata (`_fetch_repo_metadata`) and has a `_has_readme()` helper that hits a single GitHub endpoint. It does not yet fetch a file tree, so it needs a new helper (following the `_has_readme` pattern) that lists repo file paths via the GitHub Git Trees API, and that list needs to be included in the metadata dict returned by `_fetch_repo_metadata`.
- `agent/tools/repo_analyzer.py` — does not exist yet. New tool module, following the shape of the existing `agent/tools/tech_detector.py` (a `BaseTool` subclass that takes a `files` list and returns a small dict), that inspects file paths and returns `{"has_tests": bool}`.
- `agent/tools/base.py` — no changes expected; reuse existing `BaseTool`/`ToolResult`.
- `agent/orchestrator.py` — `_build_plan()` conditionally schedules tools (e.g. `tech_detector` runs `if profile_data.get("files")`); `repo_analyzer` should be added the same way so it runs whenever file data is available.
- `tests/unit/test_repo_analyzer.py` — new test file, mirroring `tests/unit/test_tech_detector.py`'s structure/fixtures.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Add a `_fetch_file_tree()` helper to `github_tool.py` that calls the GitHub Git Trees API (recursive) for the repo's default branch and returns a flat list of file paths; wire it into `_fetch_repo_metadata()`'s returned dict as `files`.
2. Create `agent/tools/repo_analyzer.py` with a `RepoAnalyzer(BaseTool)` class whose `execute()` takes `{"files": [...]}` and returns `ToolResult(data={"has_tests": bool})`.
3. Implement the detection logic: true if any path has a `tests`/`test` path segment, any filename is `pytest.ini`, or any filename matches `test_*.py`.
4. Register `repo_analyzer` in the tool registry/orchestrator plan (`_build_plan` in `agent/orchestrator.py`) so it executes alongside `tech_detector` when file data is present.
5. Add unit tests covering: repo with a `tests/` dir, a `test/` dir, `pytest.ini` present, `test_*.py` files present, no test signal, and an empty file list.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** a list of file paths for a repository (`files: list[str]`), sourced from GitHub's file tree.
- **Output:** a boolean `has_tests` field added to the tool's result data, which flows into the overall analysis output alongside `primary_language`, `has_readme`, etc., for downstream scoring/feedback to consume.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- The GitHub Trees API truncates results for very large repos (`truncated: true` in the response) — a repo with a huge file tree might get partial data and a false negative on `has_tests`. Worth noting/logging but likely out of scope to fully solve here.
- Rate limiting / auth: the new file-tree call adds another GitHub API request per repo, increasing the chance of hitting unauthenticated rate limits — should reuse the existing `api_token` handling already in `github_tool.py`.
- Case sensitivity and path separators (Windows vs. POSIX-style paths from the API) need normalizing before matching directory/file names.

### Edge cases
What inputs or states should your fix handle gracefully?

- Empty or missing `files` list → `has_tests` should be `False`, not an error.
- Repo where "test" appears only as a substring (e.g. `latest_data.py`, `contest/`) but not as an actual test signal → should not false-positive; matching should be on path segments/filenames, not substrings.
- Nested test directories (e.g. `src/module/tests/test_foo.py`) → should still be detected.
- GitHub API failure fetching the file tree (404, 403, network error) → should degrade gracefully (empty file list / `has_tests: False`) rather than failing the whole analysis, consistent with how `_has_readme()` already swallows exceptions.
