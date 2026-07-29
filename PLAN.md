## Solution plan

**Issue:** [Tech detector counts vendored and build-output files, skewing
language detection — #150](https://github.com/ascherj/pathreview/issues/150)

### Understand

The tech detector reports the wrong primary language for repositories whose only
non-source code is vendored or build output.

Root cause: `TechDetector._should_skip_file()` in `agent/tools/tech_detector.py`
skips vendored/build directories using slash-wrapped substrings (`/node_modules/`,
`/build/`, `/vendor/`, `/dist/`, ...). Each pattern starts with `/`, so it only
matches when the directory appears in the middle of a path. Repository file lists
are root-relative, so a top-level path such as `node_modules/pkg/index.js` or
`build/bundle.js` has no leading slash and never matches `"/node_modules/"` /
`"/build/"`. Those files pass the filter and get counted.

Two behaviors combine to produce the visible bug:

1. Vendored/build JavaScript files are counted alongside real source.
2. `_detect_tech()` chooses the primary language with `sorted(languages)[0]`
   (alphabetical, not frequency — `languages` is a `set`, so counts are already
   discarded), and `"JavaScript"` sorts before `"Python"`.

Expected vs. actual (verified locally):

- `test_node_modules_excluded` expects `primary_language == "Python"`; actual
  `"JavaScript"`.
- `test_build_directory_excluded` expects `primary_language == "Python"`; actual
  `"JavaScript"`.
- Tool log shows `languages_count=2`, confirming vendored files are counted.

### Map

- `agent/tools/tech_detector.py` — the fix lives in `_should_skip_file()`
  (approx. lines 143-164) and its skip-pattern list. This is a private static
  method used only by `_detect_tech()` in the same file; the public
  `execute({"files": [...]}) -> ToolResult` contract does not change.
- `tests/unit/test_tech_detector.py` — the acceptance tests already exist
  (`test_node_modules_excluded`, `test_build_directory_excluded`,
  `test_vendor_files_excluded`). I will add regression cases (nested vendored
  path, Windows separators, look-alike directory names).

### Plan

1. Rewrite `_should_skip_file()` to match **path segments** instead of
   slash-wrapped substrings: normalize `\` -> `/`, split the path on `/`, and
   skip the file if any segment exactly equals a vendored/build directory name.
2. Store the directory names as a class-level `frozenset`
   (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`,
   `venv`) so the list is clear and easy to extend.
3. Run the existing tech-detector tests; confirm `test_node_modules_excluded`
   and `test_build_directory_excluded` pass and nothing else regresses.
4. Add regression tests: a nested vendored path (`src/node_modules/x.js`), a
   Windows-style path (`build\bundle.js`), and non-vendored look-alikes
   (`distribution/app.py`, `rebuild.py`) that must NOT be skipped.
5. Run `make check` (black / ruff / mypy) and `make test-unit`; be format- and
   lint-clean before opening the PR.

### Inputs & outputs

- Input: the `files` list passed to `TechDetector.execute({"files": [...]})` —
  repository-root-relative path strings.
- Output: `_should_skip_file()` returns `True` for vendored/build files whether
  the directory is at the repo root or nested, so `_detect_tech()` counts only
  first-party source. `primary_language`, `all_languages`, and `frameworks` then
  reflect the developer's own code. The public return shape is unchanged.

### Risks & unknowns

- **Substring false positives.** A naive `"build" in path` would wrongly skip
  `distribution/`, `rebuild.py`, or `mybuild/`. Segment-equality matching avoids
  this; the regression tests lock it in.
- **Path separators.** Inputs may use `/` or `\`. Normalizing before the split
  handles both; the GitHub ingestion path emits `/`, so normalization is a
  safety net rather than a correctness dependency.
- **Out-of-scope latent bug.** `sorted(languages)[0]` is alphabetical, not
  "most common." The exclusion fix alone makes issue #150's tests green, so this
  change stays minimal and does NOT rework primary-language selection. I will
  flag the alphabetical-vs-frequency behavior in the PR description as a
  potential separate follow-up so scope stays Tier-1.
- **Case sensitivity.** Directory names match case-sensitively (canonical
  lowercase), matching the current behavior and real vendored dir names.

### Edge cases

- Vendored dir at repo root: `node_modules/pkg/index.js`, `build/bundle.js` ->
  skipped.
- Vendored dir nested: `packages/web/node_modules/x.js` -> skipped.
- Windows separators: `build\generated.js` -> normalized, skipped.
- Look-alikes that must NOT be skipped: `distribution/app.py`, `rebuild.py`,
  `src/builder/main.py`.
- Empty / missing `files` key -> existing early-return unchanged
  (`primary_language == "Unknown"`).
- Unrecognized extensions -> ignored, as today.
