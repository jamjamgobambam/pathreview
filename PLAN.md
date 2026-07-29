# Solution plan

**Issue:** [#150 - Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand
`TechDetector._should_skip_file()` is supposed to exclude vendored/build files from language detection, but it checks for substrings like `"/node_modules/"` and `"/build/"` with a slash on *both* sides. This only matches when the directory appears in the middle of a path (e.g. `"src/node_modules/x.js"`). It fails for root-level paths like `"node_modules/lib/index.js"` or `"build/bundle.js"`, because there is no leading `/` before the directory name at the start of a path string. As a result, vendored/build files are counted toward language detection, and a repo with 2 Python files and 6 vendored JS files is reported as primarily JavaScript instead of Python.

Expected behavior: any file living inside a `node_modules/`, `build/`, `vendor/`, `dist/`, etc. directory — regardless of whether that directory is at the root of the path or nested deeper — should be excluded from language/framework detection.

### Map
- `agent/tools/tech_detector.py`
  - `_should_skip_file()` — core bug, needs the path-matching logic fixed
  - `_detect_tech()` — calls `_should_skip_file()`; no logic change expected here, but will re-verify filtering is applied correctly once the fix lands
- `tests/unit/test_tech_detector.py`
  - `test_node_modules_excluded` / `test_build_directory_excluded` — existing tests that should pass once fixed
  - Will likely add new test cases for nested vs. root-level skip directories

### Plan
1. Rewrite `_should_skip_file()` to check path *segments* rather than raw substrings — e.g. split `filepath` on `"/"` and check whether any segment exactly matches a skip-directory name (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`), instead of matching `"/name/"` as a literal substring.
2. Re-run `reproduce_issue_150.py` and confirm it now prints `primary_language = Python` and the assertion passes.
3. Re-run `test_node_modules_excluded` and `test_build_directory_excluded` and confirm both pass.
4. Add new unit tests for root-level skip directories (e.g. `"build/bundle.js"` with no parent folder) to prevent this specific regression from recurring, plus a nested case to confirm existing behavior still works.
5. Review the `primary_language` selection logic (`sorted(languages)[0]`) — decide whether to fix the alphabetical-vs-frequency issue in this same PR or file it as a separate follow-up issue, since it's related but not what issue #150 explicitly asks for.

### Inputs & outputs
- **Input:** `input_data["files"]` — a list of relative file path strings (forward-slash separated), e.g. `["main.py", "node_modules/lib/index.js"]`.
- **Output:** unchanged shape — a dict with `primary_language`, `all_languages`, `frameworks` — but correctness of the values depends on files being properly filtered before language detection runs.

### Risks & unknowns
- Unsure whether file paths could ever arrive with a leading `/` (absolute-style) or backslashes (Windows-style separators) — need to check how `files` is populated upstream (likely from `agent/tools/` or an ingestion step) to confirm paths are always relative and forward-slash normalized.
- The alphabetical `primary_language` selection is a separate but related bug — fixing the filtering alone won't fully guarantee correct "primary language" results in repos with multiple real languages remaining after filtering. Need to decide scope before starting implementation.
- Changing from substring matching to segment matching needs to preserve correct behavior for nested paths (e.g. `"src/vendor/lib.js"`) that currently work correctly, so the fix should not regress existing passing tests.

### Edge cases
- Root-level skip directories with no parent folder: `"build/bundle.js"`, `"node_modules/x.js"`.
- Deeply nested skip directories: `"packages/app/node_modules/pkg/index.js"`.
- Legitimate files whose *names* merely contain a skip-directory word as a substring but aren't actually inside that directory, e.g. `"src/rebuild/utils.py"` (should NOT be skipped) or `"vendor_utils.py"` (should NOT be skipped) — segment-based matching should already handle this correctly, but worth an explicit test.
- Empty file list (already handled — returns `"Unknown"`).
- A file list containing only vendored/build files and no real source files (primary language should become `"Unknown"`, not silently default to something incorrect).