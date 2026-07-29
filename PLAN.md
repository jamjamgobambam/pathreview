# Solution plan

**Issue:** Tech detector counts vendored and build-output files, skewing language detection — [#150](https://github.com/ascherj/pathreview/issues/150)

### Understand

`TechDetector._detect_tech` (`agent/tools/tech_detector.py`) is supposed to drop
vendored/generated paths — `node_modules/`, `vendor/`, `dist/`, `build/`,
`.git/`, `__pycache__/`, `.venv/`, `venv/` — before it counts languages by
file extension. The filtering happens in `_should_skip_file`, which checks
`any(pattern in filepath for pattern in skip_patterns)` against patterns like
`"/node_modules/"` — every pattern has a **leading slash**.

The `files` list the tool actually receives (see `execute`, and every test
in `tests/unit/test_tech_detector.py`) is repo-relative paths with **no**
leading slash — e.g. `"node_modules/pkg/index.js"`. Since `"/node_modules/"`
is not a substring of `"node_modules/pkg/index.js"` (the pattern demands a
`/` *before* the directory name too), `_should_skip_file` returns `False`
for these paths and they survive into the language count.

- **Expected:** a repo with a couple of `.py` files and a vendored
  `node_modules/`/`build/` tree reports `primary_language: "Python"`.
- **Actual:** the vendored `.js` files are counted, `"JavaScript"` ends up
  in the `languages` set alongside `"Python"`, and because `primary` is
  chosen as `sorted(languages)[0]` (alphabetically first, not most-frequent
  — a separate quirk, see Risks), `"JavaScript"` wins since `"J" < "P"`.

Confirmed by running the two tests that already pin this behavior:
```
pytest tests/unit/test_tech_detector.py -k "test_node_modules_excluded or test_build_directory_excluded" -v
```
Both fail on current `main`/branch tip with `AssertionError: assert 'JavaScript' == 'Python'`.

### Map

- `agent/tools/tech_detector.py`
  - `TechDetector._should_skip_file` (~line 143) — the path-matching bug,
    the only function that needs a logic change.
  - `TechDetector._detect_tech` (~line 93) — calls `_should_skip_file`;
    read-only, no change expected unless the fix needs a signature change.
- `tests/unit/test_tech_detector.py`
  - `test_node_modules_excluded` (line 66), `test_build_directory_excluded`
    (line 94) — existing tests that should pass once the fix lands, no
    edits needed unless I find they under-specify the fix.
  - `test_vendor_files_excluded` (line 81) — not currently asserting
    anything (no `assert` in the body); worth tightening while I'm in this
    file so `vendor/` is covered as rigorously as `node_modules/`/`build/`.
- No other files reference `_should_skip_file` or `TechDetector` directly
  (confirmed via `grep -rn "_should_skip_file\|TechDetector" --include=*.py`
  outside the test/source pair above only turns up the tool registration).

### Plan

1. Reproduce and document the bug (this week) — done: comment added at
   `_should_skip_file` in `agent/tools/tech_detector.py`, this PLAN.md, and
   the JOURNAL.md Week 8 entry.
2. Change `_should_skip_file` so a pattern matches whether or not the path
   has a leading slash — e.g. check the pattern both as `pattern` (mid-path)
   and as `pattern.lstrip("/")` anchored at the start of `filepath`, or
   normalize `filepath` to always start with `/` before running the
   existing `in` checks (simplest: `f"/{filepath}"` before the `any(...)`
   check, since every current pattern already assumes a leading slash and
   mid-path occurrences like `"src/vendor/x.js"` should still match).
3. Re-run `pytest tests/unit/test_tech_detector.py -v` and confirm all
   tests pass, in particular `test_node_modules_excluded` and
   `test_build_directory_excluded`.
4. Add/tighten assertions in `test_vendor_files_excluded` (and any other
   test in the file missing an `assert`) so vendor-path filtering is
   actually verified, not just exercised.
5. Run `make check` and `make test-unit`, confirm no *new* failures beyond
   the pre-existing ones documented in Risks below, then write the PR
   description per `docs/CONTRIBUTING.md`.

### Inputs & outputs

- **Input:** `input_data: dict` passed to `TechDetector.execute`, specifically
  `input_data["files"]`, a `list[str]` of repo-relative file paths (may or
  may not have a leading slash depending on caller — this is exactly the
  ambiguity the bug lives in).
- **Output:** unchanged shape — `ToolResult.data` with `primary_language`
  (str), `all_languages` (sorted list[str]), `frameworks` (sorted list[str]).
  The fix changes *which* files are filtered before this dict is built, not
  the dict's structure.

### Risks & unknowns

- **Alphabetical "primary" selection is a separate latent bug.** `primary`
  is `sorted(languages)[0]`, not the most-frequent language by file count.
  The issue's stated symptom ("JavaScript count above Python") reads like a
  frequency claim, but the code has never counted frequency — it's alphabetical.
  The two pinned tests still pass once filtering is fixed, only because
  filtering correctly leaves `{"Python"}` as the *only* language in both
  cases. I'm treating this as out of scope for #150 (the issue and its
  tests are specifically about the skip-path filter), but I'll call it out
  explicitly in the PR description so it isn't mistaken for "fixed."
- **Pattern matching could over- or under-match.** Anchoring with a leading
  `/` needs to still match nested occurrences like `"src/vendor/lib.js"`
  (currently relies on `"/vendor/"` being a substring anywhere) while also
  catching root-level occurrences like `"vendor/lib.js"`. Need a test for
  a vendored dir that isn't at the path root to make sure I don't break the
  nested case while fixing the root case.
- **Pre-existing failing tests unrelated to this issue.** Baseline run of
  `pytest tests/unit -m unit` (before any fix) shows **53 failing, 375
  passing**, across many unrelated modules (`test_review_service.py`,
  `test_resume_parser.py`, `test_pii_scrubber.py`, `test_skill_extractor.py`,
  etc.) — only 2 of the 53 (`test_node_modules_excluded`,
  `test_build_directory_excluded`) belong to this issue. I will re-run the
  full suite after the fix and confirm the failure count only drops by
  these 2 and nothing new appears, then document this baseline in the PR
  description per the Week 9 instructions.
- **`make check` currently fails on this file before any of my changes**
  (pre-existing `ruff` import-sort warning + `black` reformat flag on
  `agent/tools/tech_detector.py`, confirmed by running `make check`/`black
  --check`/`ruff check` against the unmodified file). Unrelated to `#150`;
  I'll leave it alone unless it's inside the diff hunk I'm already touching,
  to avoid unrelated scope creep, and will note it as pre-existing in the PR.

### Edge cases

- Path exactly equal to the skip directory with no children, e.g.
  `"node_modules"` (no trailing content) — shouldn't false-positive on
  something like `"my_node_modules_notes.py"`.
- Skip directory nested deeper than one level, e.g.
  `"packages/app/node_modules/lib/index.js"`.
- Skip directory at the very start vs. the middle vs. the end of the path,
  e.g. `"build/x.js"` vs `"src/build/x.js"` vs `"weird/path/build"`.
- Windows-style backslash paths, if any caller ever passes them (current
  code only checks `/`-separated patterns) — confirm whether `files` is
  guaranteed POSIX-style upstream, or whether the fix needs to normalize
  separators too.
- Empty `files` list and missing `"files"` key — already handled by
  `execute`'s early return; must not regress this while touching
  `_should_skip_file`.
