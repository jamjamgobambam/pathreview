# Solution plan

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

**Root cause.** The `TechDetector` tool guesses a repository's primary language by
counting source files per language. It is supposed to ignore vendored dependencies
(`node_modules`, `vendor`) and build output (`dist`, `build`), and it has a
`_should_skip_file()` filter meant to do exactly that. But the skip patterns were
written with **leading slashes** — `"/node_modules/"`, `"/build/"`, `"/dist/"` — and
the check was a substring match:

```python
return any(pattern in filepath for pattern in SKIP_PATTERNS)
```

`"/node_modules/" in "node_modules/lib/index.js"` is `False`, because the path does
not start with a slash. So the filter only catches these directories when they are
**nested** inside another folder, and misses them when they sit at the **top** of the
path — which is the common case.

**Expected vs. actual.** For a repo with 2 hand-written Python files and 6 bundled
JS files under `node_modules/`, the primary language *should* be reported as
`Python`. Actual behavior: the vendored JS files are counted, inflating the JS count,
and the tool reports `JavaScript`.

### Map

Files involved:

- **`agent/tools/tech_detector.py`** — the only file with logic to change.
  - `_should_skip_file()` — the broken filter (rewrite this).
  - `_detect_tech()` — calls the filter via a list comprehension (no change needed).
- **`tests/unit/test_tech_detector.py`** — the two failing tests that define
  correct behavior (`test_node_modules_excluded`, `test_build_directory_excluded`).
  Read-only reference; success = make these green without breaking the other 25.

### Plan

1. Replace the leading-slash substring patterns with a `SKIP_DIRECTORIES` set of bare
   directory names (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`,
   `.venv`, `venv`).
2. Rewrite `_should_skip_file()` to normalize Windows separators (`\` → `/`), split
   the path into segments, and skip the file if **any** segment is in
   `SKIP_DIRECTORIES`. This matches the directory whether it is top-level or nested.
3. Run the unit tests and confirm the two target tests pass and the other 25 still do.
4. Run `make check` (ruff + black + mypy) so the change satisfies the pre-commit hooks.

### Inputs & outputs

- **Input:** a list of repository file paths (strings), e.g.
  `["node_modules/lib/index.js", "main.py", "build/out.js", "app.py"]`.
- **Output:** the same `_detect_tech()` result dict, but with vendored/build files
  correctly excluded — so `primary_language` reflects only the code the user wrote
  (`"Python"` in the example above), not bundled dependencies.

### Risks & unknowns

- **Over-matching a legitimate folder.** A real source directory literally named
  `build/` or `dist/` would also be skipped. Acceptable — that matches the issue's
  intent and how tools like GitHub Linguist behave — but worth noting.
- **Path separators.** Windows paths use `\`. The rewrite normalizes them before
  splitting; if a caller passes an already-mixed path this stays correct.
- **Secondary latent bug (out of scope).** `primary = sorted(languages)[0]` picks the
  **alphabetically first** language, not the most common one. The two failing tests
  pass with the exclusion fix alone, so I am keeping scope to the vendored/build
  exclusion the issue describes and *not* touching the primary-language tie-break
  unless a test demands it.

### Edge cases

- Directory at the **top** of the path: `node_modules/lib/index.js` → skipped.
- Directory **nested** deeper: `packages/app/build/bundle.js` → skipped.
- **Windows** separators: `node_modules\lib\index.js` → skipped.
- A filename that merely **contains** the word but isn't a directory:
  `my_build_notes.py` → **not** skipped (segment match, not substring).
- Empty file list → returns `Unknown` (existing behavior, unchanged).
