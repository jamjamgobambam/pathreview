## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output — https://github.com/ascherj/pathreview/issues/50

### Understand
The expected behavior is that `has_tests` reflects whether a scanned GitHub
repository actually contains tests. The detection logic for this already
exists in `ingestion/parsers/repo_analyzer.py` (`_detect_tests`), checking
for indicators like a `tests/` directory, `pytest.ini`, or `test_*.py` files.
The actual (broken) behavior is that `has_tests` is always `False`, because
the `file_structure` field it depends on is never populated anywhere in the
pipeline — `agent/tools/github_tool.py`, which builds the repo metadata dict,
never fetches or includes a file listing. I confirmed this with a real
reproduction against the pathreview repo itself, and with two committed
pytest tests in `tests/unit/test_repo_analyzer.py`.

### Map
- `agent/tools/github_tool.py` — needs a new method to fetch the repo's file
  tree from GitHub (likely via the Git Trees API:
  `GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1`), and needs to add
  a `file_structure` key to the metadata dict returned by `_fetch_repo_metadata`.
- `ingestion/parsers/repo_analyzer.py` — no logic changes expected; `_detect_tests`,
  `_detect_ci`, and `_detect_tech_stack` should all start working correctly
  once real `file_structure` data flows in.
- `tests/unit/test_repo_analyzer.py` — existing reproduction tests; will
  extend or add integration-style tests once the fix is in place.

### Plan
1. Add a method to `GitHubTool` (e.g. `_fetch_file_structure`) that calls
   GitHub's Git Trees API to get a recursive file listing for the repo.
2. Flatten the tree response into a newline-joined string matching the
   format `_detect_tests`/`_detect_ci` expect (they call `str(...).lower()`
   on `file_structure`).
3. Add `"file_structure": self._fetch_file_structure(username, repo_name)`
   to the metadata dict in `_fetch_repo_metadata`.
4. Update/extend tests to confirm `has_tests` now correctly returns `True`
   for repos with tests and `False` for repos without, using real API calls
   or mocked responses.
5. Manually verify against a couple of real repos (one with tests, one
   without) to confirm no false positives/negatives.

### Inputs & outputs
**Input:** a GitHub `username` and `repo_name`, as already accepted by
`GitHubTool.execute()`.
**Output:** the existing metadata dict, now including an accurate
`file_structure` string, which flows into `RepoAnalyzer.parse()` and
produces a correct `has_tests` boolean (also fixes `has_ci` and
`tech_stack` as a side effect, since they depend on the same field).

### Risks & unknowns
- The Git Trees API can be paginated/truncated for very large repos
  (GitHub returns `truncated: true`) — need to handle that gracefully
  rather than silently missing files.
- This adds an extra GitHub API call per repo analyzed, on top of existing
  metadata and README calls — could hit rate limits faster, especially
  unauthenticated. Need to confirm whether `GitHubTool` is used with an
  authenticated token in practice.
- `file_structure` format: current code assumes a flat string (via
  `str(...).lower()`), so the new fetch method must produce a string,
  not a list, to avoid changing `repo_analyzer.py`.
- Fixing `file_structure` will also change `has_ci` and `tech_stack` output
  for any already-analyzed repos — worth confirming this is in scope and
  not an unintended expansion of the issue.

### Edge cases
- Empty repositories (no files at all) — should return `has_tests: False`
  without erroring.
- Repos where the file-tree API call fails (404, rate limit) — should
  degrade gracefully (e.g. `file_structure` empty string, `has_tests: False`)
  rather than crashing the whole analysis.
- Very large repos where the tree response is `truncated: true`.
- Repos using non-standard test directory names not covered by the
  existing `_detect_tests` indicators (out of scope to fix, but worth noting).
