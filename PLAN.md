## Solution plan

**Issue:** Tech detector counts vendored and build-output files, skewing language detection — https://github.com/ascherj/pathreview/issues/150

### Understand

The `tech_detector` agent tool infers a repository's primary language by
scanning file extensions, and it is meant to ignore third-party and generated
code (`node_modules/`, `build/`, `vendor/`, `dist/`, `.venv/`, etc.).

The root cause is a path-matching bug in `TechDetector._should_skip_file`
(`agent/tools/tech_detector.py`). The skip patterns are all written with a
leading slash — `"/node_modules/"`, `"/build/"`, `"/vendor/"` — and the check
is a plain substring test: `pattern in filepath`. Repository file lists use
root-relative paths, so a root-level vendored directory arrives as
`node_modules/lib/index.js` (no leading slash). `"/node_modules/"` is **not** a
substring of `node_modules/lib/index.js`, so the file is never skipped. Windows
paths using backslashes (`node_modules\lib\index.js`) also never match.

- **Expected:** vendored/build files are dropped before counting; for 2 Python
  files + 6 vendored JS files, `primary_language == "Python"`.
- **Actual (pre-fix):** nothing is excluded, the 6 JS files dominate, and
  because the primary language is chosen as the alphabetically-first of the
  detected set, `primary_language == "JavaScript"`.

### Map

- **`agent/tools/tech_detector.py`** — the only source file that needs to
  change. Specifically the static method `_should_skip_file(filepath)` (the
  `skip_patterns` list and the final `return any(...)`). `_detect_tech` calls it
  to build `filtered_files`; no change needed there.
- **`tests/unit/test_tech_detector.py`** — existing tests that encode the
  expected behavior: `test_node_modules_excluded`, `test_build_directory_excluded`,
  `test_vendor_files_excluded`. These fail pre-fix and are the definition of done.
- **`repro_issue_150.py`** (root) — standalone reproduction script.

### Plan

1. **Reproduce** the bug locally: run the issue snippet and the two target
   tests against the current code; confirm `JavaScript` / 2 failing tests. *(done)*
2. **Normalize the path before matching** in `_should_skip_file`: convert
   Windows separators to `/` and prepend a leading `/` so root-level directories
   match the same slash-delimited patterns as nested ones. Keep the existing
   `skip_patterns` list unchanged.
3. **Verify** the two target tests pass and the full `test_tech_detector.py`
   suite (27 tests) stays green; re-run `repro_issue_150.py` and confirm
   `Python`.
4. **Run repo checks** — `make check` (ruff + black + mypy) and `make test-unit`
   — so the change is PR-ready per CONTRIBUTING.md.

### Inputs & outputs

- **Input:** `input_data["files"]` — a list of repository file-path strings
  (root-relative, possibly with `/` or `\` separators, directories at any depth).
- **Output:** the `ToolResult.data` dict — `primary_language`, `all_languages`,
  `frameworks`. The fix changes only which files are counted; the output shape is
  unchanged. For the issue's input, `primary_language` flips `JavaScript`→`Python`
  and `all_languages` drops `JavaScript`.

### Risks & unknowns

- **Over-matching:** prepending `/` and substring-matching could in theory skip a
  legitimately-named path segment (e.g. a real source folder literally called
  `build/`). This matches the tool's existing intent (those directory names are
  treated as non-source), so it is acceptable, but worth noting.
- **Out of scope but related:** `primary_language` is documented as "most common"
  yet is actually the alphabetically-first entry of a `set` — occurrences are
  never counted. This is a separate latent bug; #150 does not require fixing it,
  and all existing tests pass without touching it. Flagging rather than expanding
  scope.
- **Cross-platform:** need to make sure the normalization handles `\` so the tool
  behaves the same on Windows and POSIX.

### Edge cases

- Root-level vendored/build dir: `node_modules/lib/index.js` → skipped.
- Nested vendored dir (already worked): `src/node_modules/x.js` → still skipped.
- Windows separators: `node_modules\lib\index.js` → skipped.
- A real source file whose name merely *contains* a token, e.g.
  `my_node_modules_helper.py` → **not** skipped (no surrounding slashes).
- A top-level source file: `main.py` → normalized to `/main.py`, not skipped.
- Empty / missing `files` input → unchanged existing behavior (`Unknown`).
