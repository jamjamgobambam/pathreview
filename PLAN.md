# Solution Plan — Issue #150

**Issue:** [#150 — Tech detector counts vendored and build-output files, skewing
language detection](https://github.com/ascherj/pathreview/issues/150)
**Tier:** 1 (good first issue)
**Branch:** `fix/150-exclude-vendored-build-files`

---

## 1. Problem

`agent/tools/tech_detector.py` infers a repository's primary programming language
from file extensions. It is supposed to ignore vendored dependencies and build
output, but it fails to exclude **top-level** `node_modules/` and `build/`
directories. Their bundled/third-party JavaScript then gets counted, so a
mostly-Python repo is misreported as JavaScript.

## 2. How to reproduce

**Failing tests (the acceptance target):**
```bash
.venv/bin/pytest tests/unit/test_tech_detector.py \
  -k "node_modules_excluded or build_directory_excluded" -v
```
- `tests/unit/test_tech_detector.py::test_node_modules_excluded`
- `tests/unit/test_tech_detector.py::test_build_directory_excluded`

Both assert `primary_language == "Python"` and (before the fix) get
`"JavaScript"`.

**Manual repro (from the issue):**
```python
from agent.tools.tech_detector import TechDetector
t = TechDetector()
files = ['main.py','core/app.py','node_modules/lib/index.js',
         'node_modules/lib/util.js','node_modules/x/a.js','node_modules/y/b.js',
         'build/bundle.js','build/vendor.js']
print(t.execute({'files': files}).data['primary_language'])
# Before fix: 'JavaScript'   Expected: 'Python'
```

## 3. Root cause

`_should_skip_file()` (tech_detector.py, ~L143–164) matches skip patterns as
**slash-wrapped substrings**:
```python
skip_patterns = ["/node_modules/", "/build/", ...]
return any(pattern in filepath for pattern in skip_patterns)
```
A top-level path like `node_modules/lib/index.js` has **no leading slash**, so
`"/node_modules/"` is not a substring of it → the file is not skipped → its `.js`
extensions are counted.

## 4. Proposed solution

Match on **path segments** instead of slash-wrapped substrings: split the path on
`/` and skip the file if any segment is a known vendor/build directory. This
handles both top-level (`node_modules/...`) and nested (`src/vendor/...`) cases.

```python
skip_dirs = {"node_modules", "vendor", "dist", "build",
             ".git", "__pycache__", ".venv", "venv"}
return any(segment in skip_dirs for segment in filepath.split("/"))
```

## 5. Files to touch

| File | Change |
|---|---|
| `agent/tools/tech_detector.py` | Rewrite `_should_skip_file()` to segment-based matching (~10 lines, one method) |
| `tests/unit/test_tech_detector.py` | No change — the two failing tests already define "done" |

## 6. Step-by-step

1. Reproduce: run the two failing tests, confirm red.
2. Edit `_should_skip_file()` to segment-based matching.
3. Run the two target tests → green.
4. Run the whole `tests/unit/test_tech_detector.py` → no regressions.
5. Run the issue's manual repro → `Python`.
6. Commit as a single `fix(agent): ...` (Conventional Commits), push, open PR.

## 7. Testing & validation

- Target tests: `test_node_modules_excluded`, `test_build_directory_excluded`.
- Regression guard: full `tests/unit/test_tech_detector.py` (27 tests).
- Behavioral check: the issue's manual repro returns `Python`.

## 8. Risks & unknowns

- **Over-exclusion:** matching a bare segment could skip a legitimately-named
  file/dir (e.g. a source file literally named `build`). Low impact — such a file
  has no recognized language extension anyway; acceptable for this tool.
- **Path separators:** the codebase uses `/`-style (GitHub) paths, matching the
  original code. Windows `\` paths are out of scope (unchanged from before).
- **Pre-existing repo state:** the wider unit suite has ~51 failures in unrelated
  modules that also fail on `main`; they are not caused by this change and are
  not in scope.

## 9. Out of scope (candidate for a separate issue)

Primary language is selected **alphabetically** (`sorted(languages)[0]`), not by
file count, despite the "most common" comment. Fixing the exclusion bug alone
satisfies both acceptance tests; bundling a behavior change would make the PR
harder to review. Recommend filing this as its own issue.

## 10. Status

Reproduced and implemented on this branch (commit `f413972`); all target tests
pass. This document records the plan/approach; see `JOURNAL.md` for the log.