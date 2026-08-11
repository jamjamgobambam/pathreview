## Solution plan

**Issue:** Add a `has_tests` boolean to the repo analysis output — https://github.com/ascherj/pathreview/issues/50

### Understand
The issue description suggests `has_tests` needs to be added from scratch, but on inspection, `RepoAnalyzer._detect_tests()` in `agent/tools/repo_analyzer.py` already implements the detection logic and already includes `has_tests` in its output metadata. The actual root cause is upstream: `GitHubTool._fetch_repo_metadata()` in `agent/tools/github_tool.py` never fetches or includes a `file_structure` key when building its metadata dict. Since `_detect_tests()` reads `repo_data.get("file_structure", "")`, it always receives an empty string in the real pipeline, so `has_tests` silently evaluates to `False` regardless of the repo's actual contents. Expected behavior: `has_tests` should reflect the real presence of test files/directories in the repo. Actual behavior: `has_tests` is always `False`.

### Map
- `agent/tools/github_tool.py` — `_fetch_repo_metadata()` needs to fetch the repo's file tree and add it to the metadata dict as `file_structure`. Likely needs a new helper method, e.g. `_get_file_structure()`, using GitHub's Git Trees API (`/repos/{owner}/{repo}/git/trees/{branch}?recursive=1`).
- `ingestion/parsers/repo_analyzer.py` — no changes expected to `_detect_tests()` itself, since its logic is already correct; it just needs real data.

### Plan
1. Add a `_get_file_structure()` method to `GitHubTool` that calls the GitHub Trees API and returns a flat list/string of file paths in the repo.
2. Wire `file_structure` into the `metadata` dict returned by `_fetch_repo_metadata()`.
3. Handle API errors gracefully (e.g. empty repos, repos with no default branch, rate limiting) so the whole tool doesn't fail if the tree fetch fails — fall back to an empty file_structure rather than raising.
4. Write a test confirming `has_tests` is `True` for a known repo with tests and `False` for one without, exercising the full `GitHubTool` → `RepoAnalyzer` pipeline (not just `RepoAnalyzer` in isolation).
5. Manually verify against a couple of real GitHub repos (one with tests, one without) to sanity-check the fix end-to-end.

### Inputs & outputs
**Input:** a GitHub username + repo name (as already accepted by `GitHubTool.execute()`).
**Output:** the existing metadata dict, now including an accurate `file_structure` key, which allows `has_tests` (and also `has_ci`, which has the same problem) to reflect reality instead of always being `False`.

### Risks & unknowns
- Large repos: the recursive tree API could return a huge number of files — need to check if GitHub truncates results (it does, via a `truncated` field in the response) and decide how to handle that.
- Rate limiting: an extra API call per analysis run means faster rate-limit exhaustion for unauthenticated requests — worth checking if `api_token` is already used consistently here.
- Default branch: need to fetch the repo's actual default branch name rather than assuming `main`, since some repos still use `master` or something else.
- This same fix likely also repairs `has_ci`, which reads from the same broken `file_structure` field — worth confirming that's in scope or flagging it as a related but separate fix.

### Edge cases
- Empty repository (no files at all)
- Repository with a test framework other than pytest (e.g. unittest-only, no `pytest.ini`)
- Very large monorepos where the tree response is truncated
- Private repos or repos where the API token lacks access