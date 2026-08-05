## Solution plan

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

**Root cause:** `_should_skip_file()` in `agent/tools/tech_detector.py`
(~L143–164) matches skip patterns as slash-wrapped substrings, e.g.
`"/node_modules/" in filepath`. A **top-level** path such as
`node_modules/lib/index.js` has no leading slash, so `"/node_modules/"` is not a
substring of it and the file is **not** skipped. Its `.js` extension then gets
counted toward language detection.

**Expected vs. actual:** For a repo of 2 Python files + 6 vendored/bundled JS
files (in `node_modules/` and `build/`), the tool should report
`primary_language = "Python"`. **Actual:** it reports `"JavaScript"` because the
vendored JS files are counted.

### Map

- **`agent/tools/tech_detector.py`** — the only file I expect to change.
  - `TechDetector._should_skip_file()` — the buggy exclusion helper (the fix).
  - `TechDetector._detect_tech()` — calls `_should_skip_file()` to filter the
    file list before counting extensions (context; no change needed).
- **`tests/unit/test_tech_detector.py`** — already contains the two failing
  tests (`test_node_modules_excluded`, `test_build_directory_excluded`); no
  change expected — they define "done".

### Plan

1. Reproduce: run the two failing tests + the issue's manual repro; confirm
   `JavaScript` is returned.
2. Replace the slash-wrapped substring list in `_should_skip_file()` with a set
   of skip-dir names and match on **path segments** (`filepath.split("/")`).
3. Run the two target tests → green; run the full `test_tech_detector.py` → no
   regressions; re-run the manual repro → `Python`.
4. Commit as one `fix(agent): ...` (Conventional Commits) and push.

### Inputs & outputs

- **Input:** `_should_skip_file(filepath: str)` — a single repository file path
  (forward-slash separated), e.g. `"node_modules/lib/index.js"` or
  `"src/main.py"`.
- **Output:** `bool` — `True` if the file is inside a vendor/build directory and
  should be excluded from detection, else `False`. Downstream, this makes
  `_detect_tech()` count only genuine source files, so `primary_language`
  reflects the real code.

### Risks & unknowns

- **Over-exclusion:** a source file/dir literally named like a skip word (e.g. a
  file named `build`) would be skipped. Low impact — it has no recognized
  language extension anyway.
- **Path separators:** assumes `/`-style GitHub paths (same assumption as the
  original code). Windows `\` paths are out of scope.
- **Repo baseline:** ~51 unit tests fail in unrelated modules on `main` already;
  not caused by this change and out of scope.
- **Unknown:** whether the maintainer also wants the separate "primary language
  should be most-common, not alphabetical" defect addressed — I plan to keep it
  out of scope and suggest a separate issue.

### Edge cases

- Top-level vendored/build dir: `node_modules/lib/x.js`, `build/a.js` → skipped.
- Nested vendored dir: `src/vendor/x.js`, `packages/app/dist/y.js` → skipped.
- Genuine source at root or nested: `main.py`, `core/app.py` → **not** skipped.
- Absolute-ish path with leading slash: `/home/u/node_modules/x.js` → skipped.
- Empty file list → `_detect_tech` already returns `"Unknown"` (unchanged).