# Reproduction — Issue #150

**Issue:** Tech detector counts vendored and build-output files, skewing language detection
https://github.com/ascherj/pathreview/issues/150

## Summary

`tech_detector.py` excludes vendor/build directories via `_should_skip_file`, but the
skip patterns require a **leading slash** (`/node_modules/`, `/build/`, …). A directory
at the repository **root** has no leading slash, so the pattern is not a substring and the
files are **not** skipped. Their languages are then counted as source, so a
Python project that vendors a `node_modules/` (or commits a `build/` output) is
misreported as primarily **JavaScript**.

## Steps to reproduce

### 1. Direct call — the skip filter misses top-level dirs

```bash
.venv/bin/python -c "
from agent.tools.tech_detector import TechDetector
d = TechDetector()
for f in ['node_modules/pkg/index.js', 'src/node_modules/pkg/index.js', 'build/bundle.js', 'dist/app.js']:
    print(f'{f:40} skip={d._should_skip_file(f)}')
"
```

Observed:

```
node_modules/pkg/index.js                skip=False   <- BUG (should be True)
src/node_modules/pkg/index.js            skip=True
build/bundle.js                          skip=False   <- BUG (should be True)
dist/app.js                              skip=False   <- BUG (should be True)
```

Only the *nested* case is skipped; every top-level vendored/build directory leaks through.

### 2. End-to-end — language detection is skewed

```bash
.venv/bin/python -c "
from agent.tools.tech_detector import TechDetector
files = ['src/main.py', 'utils.py', 'node_modules/a/i.js', 'node_modules/b/j.js', 'node_modules/c/k.js']
print(TechDetector().execute({'files': files}).data)
"
```

Observed (a two-file Python project reported as JavaScript):

```
{'primary_language': 'JavaScript', 'all_languages': ['JavaScript', 'Python'], 'frameworks': []}
```

### 3. Existing unit tests already fail

```bash
.venv/bin/pytest tests/unit/test_tech_detector.py -v
```

Observed:

```
tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded FAILED
tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded FAILED

>       assert data["primary_language"] == "Python"
E       AssertionError: assert 'JavaScript' == 'Python'

2 failed, 25 passed
```

## Root cause

`agent/tools/tech_detector.py`, `_should_skip_file` (lines ~153–164): skip patterns are
pre-slashed strings matched with `in`, so they only match when the directory is nested
under another path segment. Fix is tracked in `PLAN.md`.

## Environment note

Local Postgres container is remapped to host port `5434` (system Postgres already holds
`5433`); not relevant to this bug — the detector operates on a plain file-path list.