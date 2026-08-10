# Solution plan

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing
language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

`TechDetector._should_skip_file()` decides whether a repository file is
third-party or generated code and should be left out of language detection. Its
skip patterns are slash-wrapped substrings (`"/node_modules/"`, `"/build/"`,
...), so a path only matches when the directory name has a slash on **both**
sides.

Repository file listings (GitHub tree API, `git ls-files`) are repo-root
relative, so a bundled file arrives as `node_modules/package1/index.js` — no
leading slash. The substring test misses it and the file is counted.

Confirmed locally with `python -m pytest tests/unit/test_tech_detector.py`:

```
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded
2 failed, 25 passed
```

Both fail the same way: `AssertionError: assert 'JavaScript' == 'Python'`.

Direct probe of the predicate (`_should_skip_file`) narrows it further — the bug
only affects **top-level** vendored directories:

| Path | Skipped today | Should be |
|---|---|---|
| `node_modules/lib/index.js` | `False` | `True` |
| `/repo/node_modules/lib/index.js` | `True` | `True` |
| `frontend/node_modules/x.js` | `True` | `True` |

**Expected:** a vendored/build path is excluded regardless of whether it is
absolute, repo-root relative, or nested, so `primary_language` reflects the
author's own source.
**Actual:** repo-root-relative vendored paths are counted, and 2 Python files
plus 6 bundled JS files report as JavaScript.

**Related defect, deliberately out of scope.** `_detect_tech()` collects
languages into a `set` and then picks `sorted(languages)[0]`, so
"primary language" is really *alphabetically first*, not most common — despite
the comment on `agent/tools/tech_detector.py:125` saying "most common". Probe:
6 `.py` files + 1 `.js` file still returns `JavaScript`. Fixing the skip logic
alone makes both named tests pass because the vendored languages disappear from
the set entirely. Counting files by language is a behavior change beyond what
#150 describes, so I plan to raise it with the maintainer rather than fold it
into this PR.

### Map

Files I expect to touch:

- `agent/tools/tech_detector.py` — `_should_skip_file()` (lines 143–164), the
  skip-pattern list, and its docstring.
- `tests/unit/test_tech_detector.py` — the two failing tests stay as-is; add
  cases for relative/nested/absolute paths and for names that must *not* be
  skipped.
- `PLAN.md`, `JOURNAL.md` — coursework tracking.

Read but not changed:

- `agent/tools/base.py` — `BaseTool` / `ToolResult` contract that `execute()`
  returns.
- `agent/orchestrator.py:102–107` — the only caller; it passes
  `profile_data["files"]` straight through, so the fix needs no caller change.

### Plan

1. **Reproduce and pin the behavior** (done). Run the unit suite, record the two
   failures, and probe `_should_skip_file()` directly to confirm that only
   repo-root-relative paths leak.
2. **Rewrite `_should_skip_file()` to match path segments, not substrings.**
   Normalize separators, split the path, and test each segment against a set of
   skip directory names (`node_modules`, `vendor`, `dist`, `build`, `.git`,
   `__pycache__`, `.venv`, `venv`). Segment equality is what makes position in
   the path irrelevant.
3. **Guard the false positives that segment matching buys us.** Verify
   `src/rebuild.py` and `api/vendored_api.py` are still counted, and that
   `.github/workflows/test.yml` is not swallowed by the `.git` rule.
4. **Extend the unit tests** with the top-level-relative, nested, absolute, and
   must-not-skip cases from the Edge cases section.
5. **Run the full unit suite**, update the docstring to describe segment
   matching, and open a PR referencing #150.

### Inputs & outputs

- **Input:** `_should_skip_file(filepath: str) -> bool`, one path string from the
  `files` list passed to `TechDetector.execute({"files": [...]})`.
- **Output:** `True` when any path segment is a vendored/build directory, else
  `False`. Knock-on effect: `_detect_tech()` filters those files out, so
  `primary_language` and `all_languages` stop counting third-party code.
- **Unchanged:** the `ToolResult` shape (`primary_language`, `all_languages`,
  `frameworks`), the tool name, and the orchestrator call signature.

### Risks & unknowns

- **`.git` vs `.github`.** A naive substring check on `".git"` would also match
  `.github/workflows/test.yml` and break `test_github_actions_detection`
  (`tests/unit/test_tech_detector.py:132`). Segment equality avoids this, but it
  is the specific regression to watch for when the suite runs.
- **Over-eager matching on real filenames.** `src/rebuild.py` contains "build"
  and `api/vendored_api.py` contains "vendor"; both are the developer's own code
  and must keep counting. Substring matching would drop them.
- **Legitimately named source directories.** A repo with its own `build/` or
  `dist/` module directory would now be excluded. That is the issue's stated
  intent, but it is a real trade-off with no per-repo signal to distinguish them.
- **Windows separators.** I have not confirmed whether any caller can supply
  backslash paths. `agent/orchestrator.py` passes GitHub API paths (always `/`),
  so this may be unreachable — I plan to normalize anyway since it is one line.
- **Case sensitivity.** Unclear whether `Node_Modules/` should be skipped.
  Existing extension matching is already case-sensitive
  (`test_case_insensitive_extension_matching` asserts nothing), so I will keep
  the skip check case-sensitive rather than silently change a second behavior,
  and ask in the PR.

### Edge cases

The fix should handle each of these gracefully:

- `node_modules/package1/index.js` — top-level relative → skipped (the bug).
- `/home/me/repo/node_modules/x.js` — absolute → skipped (works today, must not
  regress).
- `frontend/node_modules/x.js` — nested → skipped (works today, must not
  regress).
- `src/rebuild.py`, `api/vendored_api.py`, `dist_report.py` — substring-only
  lookalikes → **not** skipped.
- `.github/workflows/test.yml` — must **not** be skipped by the `.git` rule.
- `node_modules` with no trailing path, and a trailing-slash path such as
  `build/` — must not raise.
- `""` (empty string) and a path of only separators → `False`, no exception.
- `main.py` at repo root — the common case, unaffected.
