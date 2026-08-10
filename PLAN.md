## Solution Plan

**Issue:** Add a `has_tests` boolean to the repo analysis output — https://github.com/ascherj/pathreview/issues/50

### Understand

This is a **missing-feature gap**, not a runtime bug. `GitHubTool._fetch_repo_metadata`
in `agent/tools/github_tool.py` builds the repo-analysis metadata dict and already
reports `has_readme` (computed by a `_has_readme()` helper that pings the GitHub
`/readme` endpoint), but it never reports whether the repository ships automated tests.

- **Expected:** the repo-analysis output includes a `has_tests` boolean, so downstream
  scoring/feedback can treat a visible test suite as a portfolio signal.
- **Actual:** the field is absent. Reproduced by
  `tests/unit/test_github_tool.py::test_repo_metadata_includes_has_tests`, which fails on
  `assert "has_tests" in result.data` (the dict contains `has_readme` but no `has_tests`).

### Map

- **`agent/tools/github_tool.py`** — primary change.
  - `_fetch_repo_metadata()`: add `"has_tests": self._has_tests(...)` to the `metadata`
    dict, right after `has_readme`.
  - New `_has_tests(username, repo_name, default_branch)` helper, mirroring the structure
    and error-handling of `_has_readme()`.
- **`tests/unit/test_github_tool.py`** — the reproduction test (make it pass) plus new
  positive/negative detection tests.
- **Investigate (may not change):** `core/services/review_service.py`,
  `agent/orchestrator.py`, and `api/schemas/review.py` — confirm nothing validates the
  metadata dict against a strict schema that would reject a new key, and decide whether
  `has_tests` needs to be surfaced further downstream (likely out of scope for this issue).

### Plan

1. Add `_has_tests(username, repo_name, default_branch)` to `GitHubTool`: fetch the repo
   file listing once via the GitHub git-tree API
   (`GET /repos/{u}/{r}/git/trees/{default_branch}?recursive=1`) and return `True` if it
   finds a `tests/` or `test/` directory, a `pytest.ini`, or any `test_*.py` file.
2. Thread the repo's `default_branch` (already present in `repo_json`) into the call and
   add `"has_tests"` to the returned `metadata` dict after `has_readme`.
3. Make the reproduction test pass; add unit tests for a repo **with** tests (→ True) and
   **without** tests (→ False), mocking the tree API response so there is no network call.
4. Handle failure paths gracefully — non-200 responses, rate limiting, and exceptions
   return `False` rather than raising, matching `_has_readme()`.
5. Run `make check` (ruff + black + mypy) and `make test-unit`; confirm no regressions.

### Inputs & outputs

- **Input:** the existing `execute()` inputs (`github_username`, `repo_name`); internally,
  the repo's file tree from the GitHub API.
- **Output:** the metadata dict gains `"has_tests": bool`. All existing fields are
  unchanged — this is purely additive, so no breaking changes to current callers.

### Risks & unknowns

- **Extra API call per repo** (like `_has_readme`) increases GitHub rate-limit pressure,
  especially for unauthenticated requests. Mitigate by making a **single** recursive tree
  call instead of walking directories.
- **Tree truncation:** the git-tree API returns `"truncated": true` for very large repos,
  so a `test_*.py` buried deep in a huge repo could be missed. Document this as a known
  limitation; consider a shallow contents-API fallback if it proves common.
- **Default branch:** the tree endpoint needs the repo's default branch. It's available as
  `repo_json["default_branch"]`, but I must thread it through `_fetch_repo_metadata`.
- **Scope of markers:** the issue defines Python-style markers (`tests/`, `test/`,
  `pytest.ini`, `test_*.py`). JS/other conventions (`__tests__/`, `*.spec.ts`) are out of
  scope; I'll note that explicitly so `has_tests` isn't misread as language-agnostic.
- **Downstream consumption:** unclear whether scoring should *use* `has_tests` yet — I'll
  keep this issue scoped to surfacing it in the tool output and confirm no strict schema
  rejects the new key.

### Edge cases

- Repo with **no tests** → `has_tests: False` (never an error).
- **Empty repo / 404 / 403 rate-limited / network error** → `False`, no crash (mirror
  `_has_readme`'s try/except).
- Both **`tests/`** and singular **`test/`** directories must match.
- `pytest.ini` or `test_*.py` at the repo **root vs nested** — with the recursive tree,
  match anywhere in the tree; document the rule.
- Path **case** (`Tests/` vs `tests/`) — decide and document (GitHub paths are
  case-sensitive; match the lowercase conventions named in the issue).
