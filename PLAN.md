## Solution plan

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

**Expected behavior:** Files inside vendored or build-output directories
(`node_modules/`, `vendor/`, `dist/`, `build/`, etc.) should never contribute
to a repo's detected `primary_language`, `all_languages`, or `frameworks` —
regardless of whether that directory sits at the repo root or nested inside
another directory, and regardless of whether the path uses `/` or `\`.

**Actual behavior:** `TechDetector._should_skip_file`
(`agent/tools/tech_detector.py:143-164`) checks each skip pattern
(`"/node_modules/"`, `"/vendor/"`, `"/dist/"`, `"/build/"`, `"/.git/"`,
`"/__pycache__/"`, `"/.venv/"`, `"/venv/"`) as a plain substring against the
raw file path. Because every pattern requires a leading `/`:

- A vendored directory at the **repo root** (`"node_modules/react/index.js"`)
  never matches, since there's no character before `node_modules` for the
  leading slash to land on.
- **Any Windows-style path** using `\` instead of `/` (`"node_modules\\react\\index.js"`)
  never matches at all, since the patterns only ever contain `/`.

Root cause is the substring-matching approach itself: it treats the skip list
as literal strings to search for rather than normalizing the path and
matching directory *segments*. Confirmed via reproduction in Week 8 (see
`JOURNAL.md`) — two existing unit tests already fail against this exact bug,
and a third manual repro confirms the backslash case.

### Map

Files I expect to touch:

- **`agent/tools/tech_detector.py`** — the fix itself, entirely inside
  `_should_skip_file` (lines 143-164). Likely approach: split the path on
  both `/` and `\` into segments, check membership against a set of
  directory names, rather than substring-matching slash-wrapped patterns.
- **`tests/unit/test_tech_detector.py`** — extend/fix existing tests:
  - `test_node_modules_excluded` and `test_build_directory_excluded` already
    exist and already encode the root-level case correctly (they currently
    fail) — no change needed to their bodies, they should just start passing.
  - `test_vendor_files_excluded` currently has no assertion at all — needs a
    real assertion added (`assert data["primary_language"] == "Python"`) so
    it actually exercises the vendor-exclusion path.
  - New test(s) needed for: Windows backslash paths, and for whichever
    additional directories get added to the skip list (see Risks below).
  - Since `pyproject.toml` sets `disallow_untyped_defs = true` repo-wide and
    this file currently fails `mypy`/`ruff` pre-commit hooks on ~30
    pre-existing issues (missing return-type annotations on every test
    method, a couple of unused locals), I'll need to add `-> None` to any
    test method I touch/add and clean up the specific unused-variable lines
    ruff flags, or the fix commit won't pass the pre-commit gate. I'm not
    planning to fix annotations on methods I don't otherwise touch, to keep
    the diff focused on this issue.
- No other files expected — this is a pure string/path-logic change with no
  cross-module or API-surface impact, matching the Tier 1 scope reasoning
  from Week 7.

### Plan

1. **Normalize the path** at the top of `_should_skip_file`: replace `\`
   with `/` (`filepath.replace("\\", "/")`) so downstream logic only has to
   handle one separator.
2. **Rewrite the matching logic** to check path *segments* rather than
   substrings: split the normalized path on `/` and check whether any
   segment is in a `set` of skip-directory names (`node_modules`, `vendor`,
   `dist`, `build`, `.git`, `__pycache__`, `.venv`, `venv`, plus the
   broadened additions below) — this naturally handles root-level, nested,
   and trailing-segment cases without needing leading/trailing slash
   variants at all.
3. **Broaden the skip list** per the issue's ask — add common build-output
   dirs the current list misses: `target` (Rust/Java), `.next` / `.nuxt`
   (JS framework build output), `.pytest_cache`, `.mypy_cache`, `.ruff_cache`,
   `.tox`, `.eggs`, `*.egg-info` (this last one is a suffix pattern, not a
   directory name — needs a small special case or a separate suffix check).
4. **Fix `test_vendor_files_excluded`** to add the missing assertion, and add
   new test cases: root-level vendored file (already covered by existing
   tests, should now pass), nested vendored file, and Windows-backslash
   vendored file (root-level and nested).
5. **Run the full test file** and confirm all tests pass, then run the
   broader `pytest tests/unit/` suite to confirm nothing else depended on
   the old (buggy) substring-matching behavior.

### Inputs & outputs

- **Input:** `_should_skip_file(filepath: str) -> bool` takes a single file
  path string, as produced by whatever upstream ingestion step lists repo
  files (paths may be relative, root-level, nested, or backslash-separated
  depending on OS / git listing method).
- **Output:** `True` if the file should be excluded from language/framework
  detection, `False` otherwise. No change to the function's signature or
  return type — purely an internal logic fix. Downstream, `_detect_tech`'s
  `filtered_files` list (and therefore `primary_language`, `all_languages`,
  `frameworks` in the tool's output) changes to correctly exclude vendored
  files in the previously-missed cases.

### Risks & unknowns

- **How broad should the skip list get?** The issue says "broadens the skip
  list" without specifying exactly which directories. Over-broadening risks
  accidentally excluding a directory a real project uses for source code
  (e.g., a project that happens to have a top-level `build/` directory with
  actual hand-written code, not build output). I'll keep the list to
  well-established vendor/build/cache conventions and flag it for reviewer
  feedback rather than guessing at an exhaustive list.
  - **Mitigation:** open question flagged in `JOURNAL.md`; will ask for
    early feedback via Slack/office hours before finalizing the list.
- **Segment-matching edge case:** a segment-based check means a file literally
  named `build` (no extension, at the repo root, e.g. a shell script called
  `build`) would need to not be confused with a *directory* named `build` —
  need to confirm the input file list is always full paths (dir segments
  followed by a filename) and not bare filenames, so segment-matching can't
  misfire on a same-named file. Need to check how `files` is populated
  upstream (likely `git ls-files` or similar) to confirm this assumption.
- **`.egg-info` and similar suffix-based patterns** don't fit the
  segment-matching model cleanly (they're a suffix on a directory name, e.g.
  `pathreview.egg-info/`, not an exact segment match) — may need a small
  second check (`segment.endswith(".egg-info")`) alongside the exact-match
  set, adding a bit of complexity Comment-worthy in the fix PR.
- **Pre-commit hook debt:** as noted in Map, the test file already fails
  `mypy`/`ruff` independent of this issue. Need to scope exactly how much of
  that I fix (only touched lines) vs. leave alone, to avoid an unreviewably
  large diff.

### Edge cases

- Vendored directory at the **repo root** (`"node_modules/x.js"`) — the bug
  this issue is literally about; must be excluded.
- Vendored directory **nested several levels deep**
  (`"a/b/c/node_modules/x.js"`) — already worked before the fix (has a
  leading slash), must keep working.
- **Windows backslash paths**, both root-level (`"node_modules\\x.js"`) and
  nested (`"a\\node_modules\\x.js"`) — currently broken in both forms, must
  be fixed.
- **Mixed separators in one path** (unlikely but possible depending on
  upstream normalization, e.g. `"a/node_modules\\x.js"`) — normalize-then-split
  approach from Plan step 1 handles this for free.
- A file or directory whose name merely **contains** a skip word as a
  substring but isn't the skip word itself (e.g. `"src/rebuild/main.py"`
  contains `"build"` as a substring but `"rebuild"` is not the segment
  `"build"`) — must NOT be skipped; this is exactly what motivates
  segment-based matching over substring matching, and is worth an explicit
  test case since it's the kind of regression easy to reintroduce.
- **Empty file list** and **files with no directory component**
  (`"main.py"`) — must continue to work exactly as today (no skip match,
  included normally); already covered by `test_empty_file_list`.
