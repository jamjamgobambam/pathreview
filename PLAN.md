## Solution plan

**Issue:** Tech detector counts vendored and build-output files, skewing language detection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

### Understand

The tech detector receives a list of repository file paths and uses file extensions plus known config files to identify languages and frameworks. The bug is in path filtering: generated, vendored, and dependency directories are intended to be skipped, but the original check only looked for slash-wrapped substrings such as `/node_modules/`. Relative paths like `node_modules/lib/index.js` and `build/bundle.js` do not start with a leading slash, so they are counted as real source files.

Expected behavior: dependency, vendor, build, cache, virtualenv, and git metadata paths should not influence detected languages, frameworks, or the primary language.

Actual behavior: files under paths such as `node_modules/...` and `build/...` can be counted, allowing generated JavaScript to skew the detected language set and primary language.

### Map

Files involved:

- `agent/tools/tech_detector.py`
- `tests/unit/test_tech_detector.py`

Relevant functions:

- `TechDetector._detect_tech`
- `TechDetector._should_skip_file`

### Plan

1. Add a regression test with real Python files plus ignored JavaScript paths under `node_modules` and `build`.
2. Normalize incoming paths by replacing Windows separators with `/` and lowercasing before filtering.
3. Split each normalized path into parts and skip the file when any part exactly matches an ignored directory name.
4. Count detected languages from the filtered file list so the primary language is based on real source files only.
5. Run the focused unit test suite for `tests/unit/test_tech_detector.py`.

### Inputs & outputs

Input: a dictionary passed to `TechDetector.execute` with a `files` list containing repository-relative file paths.

Output: a `ToolResult` whose `data` includes:

- `primary_language`: the most representative language after ignored paths are removed.
- `all_languages`: sorted detected languages from real source and supported config files.
- `frameworks`: sorted detected frameworks from supported config files.

### Risks & unknowns

The main risk is over-filtering legitimate project paths whose directory names match ignored names, such as a source folder literally named `vendor` or `build`. This is acceptable for this issue because these names conventionally identify dependency or generated-output directories, and the detector already intended to exclude them.

Another risk is changing primary-language behavior for mixed-language repos. The fix should preserve deterministic output by using counts and a stable tie-breaker.

### Edge cases

- Paths with no leading slash, such as `node_modules/lib/index.js`
- Nested ignored directories, such as `packages/app/build/bundle.js`
- Windows-style paths, such as `src\__pycache__\module.pyc`
- Mixed-case extensions, such as `Main.PY`
- Empty file lists
- Repositories with only ignored files
