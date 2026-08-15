## Solution plan

**Issue:** #150 — Tech detector counts vendored and build-output files, skewing language detection
https://github.com/ascherj/pathreview/issues/150

### Understand
`TechDetector._detect_tech()` is supposed to only count files that are part of the
actual project when detecting the primary language. It filters files using
`_should_skip_file()`, which checks whether a filepath contains patterns like
`"/node_modules/"`, `"/build/"`, `"/vendor/"`, etc. — each pattern has a leading
and trailing slash. However, file paths passed into the tool (as shown in the
issue's reproduction steps, e.g. `"node_modules/lib/index.js"`) often don't have
a leading slash, since they're relative paths from the repo root. Because the
pattern requires a leading `/`, the substring check fails silently, the file is
never skipped, and it gets counted toward language detection. Expected behavior:
files under vendored/build directories should be excluded regardless of whether
the path has a leading slash. Actual behavior: a repo with 2 Python files and 6
vendored JS files is reported as `primary_language: "JavaScript"` instead of
`"Python"`.

**Root cause:** `_should_skip_file()` in `agent/tools/tech_detector.py` uses
slash-anchored substring patterns that don't match relative paths lacking a
leading slash.

### Map
Files I expect to touch:
- `agent/tools/tech_detector.py` — `_should_skip_file()` method (the skip_patterns
  list and the matching logic itself need to change).
- `tests/unit/test_tech_detector.py` — contains `test_node_modules_excluded` and
  `test_build_directory_excluded`, the two named failing tests I need to make pass.

### Plan
1. Read `tests/unit/test_tech_detector.py` to see exactly what inputs and
   assertions `test_node_modules_excluded` and `test_build_directory_excluded`
   expect, so I know the exact contract I need to satisfy.
2. Rewrite `_should_skip_file()` so it matches vendor/build directory names
   regardless of a leading slash — e.g. by checking path segments (splitting on
   `/`) instead of raw substring matching, or by normalizing the path with a
   leading slash before checking.
3. Run the two named failing tests locally to confirm they now pass:
   `pytest tests/unit/test_tech_detector.py -k "node_modules or build_directory"`.
4. Manually re-run my original reproduction steps in the Python REPL to confirm
   `primary_language` now returns `"Python"` instead of `"JavaScript"`.
5. Run the full test suite for this file (`pytest tests/unit/test_tech_detector.py`)
   to make sure I didn't break any other passing test.

### Inputs & outputs
**Function I'm changing:** `_should_skip_file(filepath: str) -> bool`

**Existing behavior:** returns `True` only when a pattern like `/node_modules/`
appears as a substring of `filepath` — meaning paths without a leading slash are
never skipped.

**New behavior:** returns `True` for any path where one of the target directory
names (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`,
`venv`) appears as a full path segment, whether or not the path starts with `/`.

### Risks & unknowns
1. **Over-matching risk:** if I switch to a looser check (e.g. just `"node_modules"
   in filepath`), I could accidentally skip a legitimate file that merely contains
   that substring in its name (e.g. `my_node_modules_analyzer.py`). I need to split
   the path into segments and compare whole segments, not just substrings.
2. **Windows vs. Unix path separators:** I'm developing on Windows; I need to
   confirm whether `filepath` ever arrives with backslashes (`\`) instead of `/`,
   which would break a `/`-based split. I'll check how `files` is populated
   upstream (likely from GitHub API data, which should always use `/`).
3. **I haven't yet read the existing test file**, so my understanding of the
   exact expected fixture inputs is based only on the issue description, not the
   actual test code — I'll confirm this in Plan step 1 before finalizing the fix.

### Edge cases
- A path like `node_modules/lib/index.js` (no leading slash) → should be skipped
- A path like `/node_modules/lib/index.js` (leading slash) → should still be skipped
- A path like `src/node_modules_helper.py` (directory name is a substring, not a
  real segment) → should NOT be skipped
- A path like `build/vendor.js` → should be skipped (matches `build`)
- A path with no vendor/build segments at all (e.g. `main.py`) → should never be
  skipped