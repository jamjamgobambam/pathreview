## Solution plan

**Issue:** Tech detector counts vendored and build-output files, skewing language detection (https://github.com/ascherj/pathreview/issues/150)

### Understand
**Root cause:** `_should_skip_file` matches vendor/build dirs using patterns that require a *leading* slash — `/node_modules/`, `/build/`, `/dist/`, etc. ([tech_detector.py:153-164](agent/tools/tech_detector.py#L153-L164)). A file at the repo root like `node_modules/pkg/index.js` has no leading slash, so `/node_modules/` is not a substring and the file is **not skipped**. Only nested cases (`src/node_modules/...`) match. As a result, committed vendored/build output is counted as source, skewing the detected languages.

**Expected vs. actual:**
- Expected: files under any `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, `__pycache__/`, `.venv/`, `venv/` directory — including at the repo root — are excluded from language detection.
- Actual: only those dirs appearing *below* another directory are excluded; top-level ones leak through.

**Reproduction (confirmed):**
- `_should_skip_file('node_modules/pkg/index.js')` → `False` (should be `True`); same for `build/bundle.js`, `dist/app.js`.
- `execute({'files': ['src/main.py','utils.py','node_modules/a/i.js','node_modules/b/j.js','node_modules/c/k.js']})` → `primary_language: 'JavaScript'` (should be Python).
- Two existing tests already fail on this: `test_node_modules_excluded`, `test_build_directory_excluded`.

### Map
- [agent/tools/tech_detector.py](agent/tools/tech_detector.py) — `TechDetector._should_skip_file` (the pattern-matching logic). **Primary file to change.**
- [tests/unit/test_tech_detector.py](tests/unit/test_tech_detector.py) — two failing tests encode the expected behavior; may add root-level cases for `dist/`, `vendor/`, `.venv/`.

Files expected to touch: those two.

### Plan
1. Fix `_should_skip_file` so directory matching is anchored per path segment, not by a `/dir/` substring — e.g. split the path on `/` and check whether any segment equals a skip directory (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`). This catches top-level, nested, and Windows-separator cases uniformly.
2. Keep the skip-dir list in one place (a set of directory names) rather than pre-slashed strings.
3. Run the suite; confirm `test_node_modules_excluded` and `test_build_directory_excluded` now pass.
4. Add regression tests: root-level `dist/`, `vendor/`, `.venv/` files excluded; ensure a legitimate file whose *name* contains "build" (e.g. `src/buildutils.py`) is NOT skipped.

### Inputs & outputs
- **Input:** `input_data["files"]` — list of file-path strings (unchanged).
- **Output:** same `ToolResult` shape (`primary_language`, `all_languages`, `frameworks`); the fix only removes vendored/build files from the counted set, so `primary_language`/`all_languages` reflect real source. No API change.

### Risks & unknowns
- Segment-equality matching must not over-match legitimate files whose names merely contain a keyword (`buildbot.py`, `dist_utils.py`) — match whole path segments, not substrings.
- Backslash paths (Windows) — decide whether to normalize `\` to `/` before splitting.
- Secondary observation (out of scope for #150): `primary_language` is `sorted(languages)[0]` (alphabetical) over a `set`, not true frequency — once vendored files are excluded these tests pass, but a genuine mixed-source repo could still mis-rank. Flag for a separate issue (cf. C-16).

### Edge cases
- Vendored/build dir at repo root vs. nested vs. deeply nested — all excluded.
- File names containing a skip keyword as a substring (`rebuild.py`, `vendored_data.py`) — NOT excluded.
- Empty / missing `files` → `Unknown` (already handled).
- Mixed separators / leading `./` (`./build/x.js`) — excluded.
- A repo that is *entirely* vendored (only `node_modules/…`) → after filtering, no files remain → `primary_language: "Unknown"`.