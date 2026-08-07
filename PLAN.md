## Solution plan

**Issue:** #150 — Tech detector counts vendored and build-output files, skewing language detection
(https://github.com/ascherj/pathreview/issues/150)

### Understand
`TechDetector._detect_tech()` (agent/tools/tech_detector.py:93) is supposed to filter out
vendored/build files before counting languages, via `_should_skip_file()` (line 143). That
method checks `pattern in filepath` against a list of patterns like `"/node_modules/"`,
`"/vendor/"`, `"/build/"`, all written with a **leading slash**.

The bug: file paths coming from the repo root (e.g. `"node_modules/lib/index.js"`,
`"build/bundle.js"`) do **not** have a leading slash. The substring `"/node_modules/"` never
appears in `"node_modules/lib/index.js"`, so `_should_skip_file` returns `False` for exactly
the paths it's meant to catch, and every vendored/build file gets counted normally. With 6
JS files in `node_modules/`/`build/` vs. 2 real Python files, `JavaScript` wins as
`primary_language` instead of `Python`.

Expected behavior: any path that starts with, or contains as a full path segment, one of the
vendor/build directory names should be excluded, regardless of whether it's nested (e.g.
`src/node_modules/x.js`) or at the repo root (e.g. `node_modules/x.js`).

**Root cause:** `_should_skip_file`'s patterns assume every match is preceded by a `/`, which
is false for repo-root-relative paths.

### Map
Files I expect to touch:
- `agent/tools/tech_detector.py` — `_should_skip_file()` (line ~143-164): fix the pattern
  matching so root-level paths match too.
- `tests/unit/test_tech_detector.py` — `test_node_modules_excluded` (line 66) and
  `test_build_directory_excluded` (line 94) already exist and currently fail; they define
  "done" for this fix. I may add one more case for a root-level `vendor/` path since
  `test_vendor_files_excluded` (line 81) currently has no assertions.

### Plan
1. Confirm exact failure: run `pytest tests/unit/test_tech_detector.py -v` and record which
   tests fail and why (already done — both `test_node_modules_excluded` and
   `test_build_directory_excluded` fail because `primary_language` comes back `JavaScript`
   instead of `Python`).
2. Rewrite `_should_skip_file` to normalize the path check — e.g. split `filepath` on `/`
   and check whether any path segment exactly matches a directory name in a skip-list
   (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`),
   instead of relying on a fixed-slash substring match.
3. Update/replace the `skip_patterns` list to be directory names instead of slash-wrapped
   substrings, so both `node_modules/lib/index.js` and `src/node_modules/lib.js` match.
4. Add an assertion to `test_vendor_files_excluded` (currently missing one) to lock in
   root-level vendor exclusion too.
5. Run `pytest tests/unit/test_tech_detector.py -v` again and confirm all tests pass,
   including the two named in the issue.
6. Run `make check` (lint + format + typecheck) to make sure the change is clean.

### Inputs & outputs
**Function I'm changing:** `_should_skip_file(filepath: str) -> bool`

**Existing (broken) behavior:**
- Input: `"node_modules/lib/index.js"` → Output: `False` (should be `True`)
- Input: `"src/node_modules/lib.js"` → Output: `True` (already works, has leading `/`)

**Fixed behavior:**
- Input: `"node_modules/lib/index.js"` → Output: `True`
- Input: `"build/bundle.js"` → Output: `True`
- Input: `"src/main.py"` → Output: `False` (unaffected — must not over-match)

**Test I already have to satisfy:**
```python
def test_node_modules_excluded(self, detector):
    files = ["src/main.py", "node_modules/package1/index.js",
             "node_modules/package2/lib.js", "utils.py"]
    result = detector.execute({"files": files})
    assert result.data["primary_language"] == "Python"

def test_build_directory_excluded(self, detector):
    files = ["src/main.py", "build/generated.js", "build/bundle.js"]
    result = detector.execute({"files": files})
    assert result.data["primary_language"] == "Python"
```

### Risks & unknowns
1. **Over-matching risk:** if I switch to segment-based matching, I need to make sure a
   legitimate file like `my_vendor_utils.py` (contains "vendor" as a substring but not as a
   path segment) doesn't get incorrectly skipped. Segment-based matching (splitting on `/`
   and comparing whole segments) avoids this, but I need a test for it.
2. **`.git`/`.venv` patterns currently include a leading dot** (`.venv`, not `venv`) —
   need to check these still work correctly after refactoring away from the slash-wrapped
   substring approach, since `.git` and `venv` are different skip entries.
3. **`primary_language` tie-breaking is alphabetical, not "most common"** (line 126-129 picks
   `sorted(languages)[0]`, despite the docstring saying "most common") — this is a separate,
   pre-existing issue not mentioned in #150. I will not fix it as part of this issue, to keep
   scope contained, but I'll note it as a possible follow-up.
4. **Windows path separators:** if any file paths ever use `\` instead of `/` (unlikely given
   GitHub API always returns `/`-separated paths), segment splitting on `/` alone would miss
   them. I'll confirm the input source (GitHub API) before assuming this isn't a concern.

### Edge cases
- Root-level vendor/build dirs: `node_modules/x.js`, `build/x.js`, `vendor/x.js` → excluded
- Nested vendor/build dirs: `src/node_modules/x.js` → excluded (already worked, must not break)
- File names that merely contain a skip-word as a substring but aren't in that directory,
  e.g. `vendor_utils.py` or `rebuild/script.py` → NOT excluded (must not over-match)
- Empty file list → still returns `"Unknown"` (existing behavior, unaffected)
- A repo that is *entirely* vendored files with no real source → `all_languages` ends up
  empty and `primary_language` is `"Unknown"`; confirm this doesn't throw an error
