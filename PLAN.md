## Solution plan

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand
`_should_skip_file` in `agent/tools/tech_detector.py` is supposed to exclude
vendored/build paths before `_detect_tech` counts file extensions. It does
this by checking whether a slash-anchored pattern like `"/node_modules/"` or
`"/build/"` appears as a substring of the filepath. That only matches when
the directory is *nested* under something else — a path rooted at the repo
root, like `node_modules/lib/index.js` or `build/bundle.js`, has no leading
`/` before the directory name, so the substring never matches and the file
is not filtered.

- **Expected:** any file living inside `node_modules/`, `vendor/`, `dist/`,
  `build/`, `.git/`, `__pycache__/`, `.venv/`, or `venv/` — anywhere in its
  path, including at the root — is excluded from language detection.
- **Actual:** only nested occurrences are excluded. Root-level vendored/build
  files leak into the extension and config-file counts and can flip
  `primary_language` to the wrong value (confirmed: reports `"JavaScript"`
  for a repo that's really 2 Python files + 6 vendored JS files — see
  `scripts/repro_issue_150.py` and the Week 8 JOURNAL entry).

### Map
- `agent/tools/tech_detector.py` — the fix itself, in the `_should_skip_file`
  static method (currently lines 143–164). No other method needs to change;
  `_detect_tech` already calls `_should_skip_file` correctly and just needs
  it to return the right answer.
- `tests/unit/test_tech_detector.py` — `test_node_modules_excluded` and
  `test_build_directory_excluded` already assert the right thing and are
  currently failing; they should pass once the fix lands. `test_vendor_files_excluded`
  currently calls the detector but asserts nothing — I'll add a real
  assertion since it covers the same bug class.
- `scripts/repro_issue_150.py` — my Week 8 reproduction script. I'll leave it
  in the repo as a runnable sanity check; it should print "Not reproduced"
  once the fix is in.
- Confirmed via `grep -rn "_should_skip_file"` that it has exactly one call
  site (`_detect_tech`, same file), so the fix is self-contained.

### Plan
1. Rewrite `_should_skip_file` to split each path on `/` and check the
   *directory* segments (all path components except the final filename)
   against a `skip_dirs` set of exact names, instead of substring-matching
   slash-anchored patterns. This fixes root-level paths without changing
   behavior for already-working nested paths.
2. Run `pytest tests/unit/test_tech_detector.py -v` and confirm
   `test_node_modules_excluded` and `test_build_directory_excluded` now pass,
   with no other test in the file newly failing.
3. Add a real assertion to `test_vendor_files_excluded` (it currently exercises
   the code but checks nothing) so the vendor/build/node_modules cases are
   consistently covered.
4. Re-run `python -m scripts.repro_issue_150` and confirm the output flips
   from "BUG REPRODUCED" to "Not reproduced".
5. Run `make test-unit` (full unit suite) and `make check` (lint + format +
   typecheck) to confirm no unrelated regressions before opening the PR.

### Inputs & outputs
- **Input:** `input_data["files"]` — a flat list of relative file-path
  strings. `TechDetector` never touches the filesystem itself; whatever
  assembles the file listing (elsewhere in the agent pipeline) is the actual
  caller.
- **Output:** unchanged shape — `execute()` still returns a `ToolResult`
  with `primary_language: str`, `all_languages: list[str]`,
  `frameworks: list[str]`. Only the *values* change for inputs that contain
  root-level vendored/build paths — no schema/API change, so nothing
  downstream of `TechDetector` should need to change.

### Risks & unknowns
- **Filename collisions:** segment-based matching must only check directory
  components, not the final filename — otherwise a real source file
  literally named `build` or `vendor` (no extension) at the repo root would
  be wrongly skipped. I'm checking `parts[:-1]`, not all parts, specifically
  to avoid this; adding a test case for it (see Edge cases).
- **Scope of the skip-dir list:** I'm not expanding the existing list
  (`node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`,
  `venv`) to cover other ecosystems (e.g. `target/` for Rust/Java, `bin/`,
  `obj/` for .NET) — that's a reasonable follow-up but not what #150 asks
  for, and adding it unasked would widen the diff beyond the issue.
  Flagging this as a conscious boundary, not an oversight.
- **Other tools with similar logic:** haven't audited whether other agent
  tools duplicate a similar path-skip pattern that has the same bug — out of
  scope for this issue, but worth a one-line mention in the PR description
  in case a maintainer wants a follow-up issue filed.

### Edge cases
- Root-level vendored dir (the actual bug): `node_modules/lib/index.js` →
  should be skipped.
- Nested vendored dir (already correct today): `src/vendor/lib.js` → should
  remain skipped.
- A file literally named after a skip directory, no extension, at the repo
  root: `build` → should **not** be skipped (it's a file, not a directory).
- Skip-directory name as a substring of an unrelated name:
  `rebuild/notes.py`, `vendor-scripts/setup.py` → should **not** be skipped
  (a path segment must equal the skip name exactly, not merely contain it).
- Empty file list → already short-circuited by the early-return branch in
  `execute()`; unaffected by this fix.
- Backslash-delimited (Windows-style) paths → out of scope. The rest of
  `tech_detector.py` already assumes forward slashes (e.g. `filepath.endswith(ext)`
  string checks), so I won't special-case backslashes unless a test demands it.
