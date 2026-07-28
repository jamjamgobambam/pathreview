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