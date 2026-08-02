# Issue #150 Reproduction

## Issue

[Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

## Environment

- Operating system: Windows
- Shell: PowerShell
- Python environment: Project `.venv`
- Working branch: `fix/150-ignore-vendored-build-files`

## Reproduction command

```powershell
python -m pytest `
  tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded `
  tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded `
  -v
```

## Observed behavior

Both targeted tests fail. TechDetector reports JavaScript as the primary
language even though the JavaScript files are located only inside root-level
node_modules/ or build/ directories.

The current path filtering uses patterns such as /node_modules/ and
/build/. Relative repository paths such as node_modules/lib/index.js and
build/bundle.js do not contain a leading slash, so they remain in the file
list used for language detection.

## Expected behavior

Files inside dependency, vendor, and generated-output directories should be
removed before language and framework detection. For the reproduction inputs,
Python should be the primary language, and JavaScript should not be detected
from the excluded files.

## Reproduction result

The issue is reproducible locally and appears to originate in
TechDetector._should_skip_file() in agent/tools/tech_detector.py.
