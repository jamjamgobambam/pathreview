## Solution plan

**Issue:** Tech detector counts vendored and build-output files, skewing language detection ([#150](https://github.com/ascherj/pathreview/issues/150))

### Understand
`tech_detector.py` is supposed to ignore files under vendor/build directories (`node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, `__pycache__/`, `.venv/`, `venv/`) when detecting a repo's primary language. Actual behavior: `_should_skip_file` matches skip patterns as substrings requiring a leading slash (e.g. `"/node_modules/"` in filepath). Root-relative paths like `node_modules/lib/index.js` or `build/bundle.js` have no leading slash, so the substring check never matches and these files are never filtered. Result: a Python repo with a few vendored/bundled JS files gets misdetected as primarily JavaScript.

Expected: files inside any of the listed directories, at any depth (root-level or nested), should be excluded from language detection.

### Map
- `agent/tools/tech_detector.py` — `_should_skip_file` (~line 143-164), only function needing a change.
- `tests/unit/test_tech_detector.py` — `test_node_modules_excluded`, `test_build_directory_excluded` already encode the expected behavior; no test changes needed, just need to pass.

### Plan
1. Replace substring/slash-based matching in `_should_skip_file` with path-segment matching: split `filepath` on `/` and check if any directory segment (all parts except the filename) is in the skip-dir set.
2. Keep the same set of directory names to skip: `node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`.
3. Run `.venv/bin/pytest tests/unit/test_tech_detector.py -v -m unit` and confirm all 27 tests pass.
4. Run the exact issue repro snippet manually to confirm `primary_language == 'Python'`.
5. Run full unit suite (`.venv/bin/pytest tests/unit -v -m unit`) to check for regressions elsewhere.

### Inputs & outputs
Input: `list[str]` of repo file paths (root-relative, forward-slash separated), passed via `execute({'files': [...]})`.
Output: unchanged shape, `ToolResult.data` dict with `primary_language`, `all_languages`, `frameworks` — only the *values* should change (vendor/build files properly excluded from the counts feeding these).

### Risks & unknowns
- Segment-based matching must only check directory segments (`parts[:-1]`), not the filename itself, or a file literally named `build` (no extension) would be wrongly skipped.
- Windows-style paths (`\`) aren't handled by either old or new code — out of scope, existing code already assumes `/`.
- Case sensitivity: skip-dir names aren't lowercased; a directory named `Node_Modules` wouldn't match. Existing tests don't cover this, so not changing unless asked.

### Edge cases
- Root-level vendor dirs: `node_modules/lib/index.js` (this is the actual bug case).
- Nested vendor dirs: `src/node_modules/lib/index.js`.
- Empty file list and missing `files` key (already handled earlier in `execute`, unaffected by this fix).
- File names that merely contain a skip-word as substring but aren't in that directory, e.g. `my_vendor_notes.py` or `rebuild/script.py` — should NOT be skipped (segment match avoids this false-positive; the old substring approach without leading slash would have wrongly caught these too).
