## Solution plan

**Issue:** [Add a `has_tests` boolean to the repo analysis output #50](https://github.com/ascherj/pathreview/issues/50)

### Understand

The repo-analysis output is supposed to tell a reviewer whether a portfolio
project has automated tests — "a strong portfolio signal" per the issue.
Expected: the metadata returned by repo analysis includes a `has_tests`
boolean, true when the repo has a `tests/`/`test/` directory, a
`pytest.ini`, or `test_*.py` files.

Actual (confirmed via reproduction, see `tests/unit/test_github_tool.py` and
commit `57646a9`): `agent/tools/github_tool.py` — the tool the live agent
orchestrator actually calls (`agent/orchestrator.py:94`) — never computes or
includes `has_tests` at all. It has an analogous `has_readme` check but no
test-detection equivalent, and never fetches any file/directory listing to
check against.

There's a second, separate implementation in
`ingestion/parsers/repo_analyzer.py` (`_detect_tests`) that *does* have
test-detection logic, but it depends on `repo_data["file_structure"]`, which
nothing in the codebase ever populates — it always evaluates against `""`.
I also confirmed this parser's `ingest_repo_metadata` caller in
`ingestion/pipeline.py` has zero callers anywhere in the app, so this whole
path is currently unreachable from the running application. It's dead code
twice over, not just a broken feature — so it's out of scope for this fix
beyond the reproduction note already left inline (`ingestion/parsers/repo_analyzer.py:123-124`).

The issue's file list (from `scripts/issues_manifest.json`, entry `C-10`)
names `agent/tools/repo_analyzer.py`, but that path has never existed in git
history — it's a stale reference, presumably meant to be
`ingestion/parsers/repo_analyzer.py`. Given the dead-code finding above,
this doesn't change the plan: the real fix belongs in `github_tool.py`.

### Map

Files I expect to touch:
- `agent/tools/github_tool.py` — add test detection, wire `has_tests` into
  `_fetch_repo_metadata`'s returned dict.
- `tests/unit/test_github_tool.py` — extend the existing reproduction test
  file with cases for the new detection logic (already has one failing test
  from Week 8; it should pass once this lands, plus new cases for
  false/true variations).

Not touching (decided out of scope, see Understand):
- `ingestion/parsers/repo_analyzer.py` — dead code, unreachable from the app.

### Plan

1. Add a `_has_tests(username, repo_name)` method to `GitHubTool`, modeled
   on the existing `_has_readme` pattern: fetch the repo's root directory
   listing via `GET /repos/{username}/{repo_name}/contents` (one API call),
   and check the returned entry names for test indicators (`tests`, `test`,
   `pytest.ini`, or any name matching `test_*.py`).
2. Wire `has_tests` into the `metadata` dict built in `_fetch_repo_metadata`,
   alongside `has_readme`.
3. Handle the request-failure path the same way `_has_readme` does (return
   `False` on any exception, e.g. repo not found or rate-limited) so a
   partial failure doesn't break the whole tool call.
4. Extend `tests/unit/test_github_tool.py`: keep the existing test (repo
   with tests → `has_tests` present), add a case for a repo with no test
   indicators → `has_tests is False`, and a case verifying the GitHub API
   call failure path still returns `success=True` overall with
   `has_tests=False` rather than blowing up the whole fetch.
5. Run the full `tests/unit/` suite plus `mypy`/`ruff`/`black` (pre-commit)
   to confirm nothing else regresses.

### Inputs & outputs

**Input:** `github_username` and `repo_name` (already the tool's existing
input shape — unchanged).

**Output:** the existing `metadata` dict gains one new key, `has_tests: bool`.
No other keys change shape. Downstream consumers (`agent/orchestrator.py`'s
`tool_results`) pass this dict through generically, so no other file needs
to change for the field to propagate into review generation.

### Risks & unknowns

- **Extra API call cost/rate limits:** this adds one more GitHub API request
  per repo analyzed (root contents listing), on top of the existing repo
  metadata + README HEAD requests. For unauthenticated requests GitHub's
  rate limit is already tight (60/hr); need to confirm this doesn't push
  typical usage over the limit in practice, or at least fail gracefully
  (already true via the try/except pattern) — need to spot check.
- **Root-level-only detection:** checking only the repo root won't catch
  test directories nested deeper (e.g. `backend/tests/`). This matches the
  issue's literal ask (top-level indicators) but is a real limitation I
  should note in the PR description, not silently paper over.
- **`test_*.py` glob matching:** GitHub's contents API returns filenames,
  not a full recursive tree, so this only catches top-level files matching
  `test_*.py` — same root-only caveat as above.
- **Unauthenticated vs authenticated requests:** haven't yet checked whether
  `GitHubTool` is ever constructed with `api_token` set in practice, which
  would affect real-world rate-limit risk. Need to check this in Week 9
  before finalizing the implementation.

### Edge cases

- Repo has no `tests`/`test` dir, no `pytest.ini`, no `test_*.py` files →
  `has_tests: False`.
- Repo is empty (no files at all) → contents call may 404; should behave
  like `_has_readme` does on 404 and return `False`, not raise.
- Repository not found / rate-limited (404/403 from the *primary* metadata
  call) → already short-circuits before test detection runs; no change
  needed here.
- Case sensitivity — GitHub is case-preserving but not always
  case-sensitive for paths on some filesystems; match indicator names
  case-insensitively the same way `ingestion/parsers/repo_analyzer.py`'s
  (dead) implementation already lowercases before comparing.
