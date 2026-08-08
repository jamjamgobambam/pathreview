## Solution plan

**Issue:** [Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

The `TechDetector` currently counts every file extension in the provided file list when determining the primary programming language. It does not filter out files located inside dependency or generated-output directories such as `node_modules/` and `build/`. As a result, third-party JavaScript files or generated bundles can outnumber the repository's real source files and cause the detector to return JavaScript as the primary language even when the project itself is primarily Python.

The expected behavior is for vendored dependencies and build artifacts to be ignored before language counts are calculated. The actual behavior is that those files are included in the counts.

### Map

The main files involved are:

- `agent/tools/tech_detector.py`
  - Contains the `TechDetector` implementation.
  - Responsible for analyzing file paths and determining language counts.
- `tests/unit/test_tech_detector.py`
  - Contains the failing tests:
    - `test_node_modules_excluded`
    - `test_build_directory_excluded`

I expect the implementation change to be limited mainly to `agent/tools/tech_detector.py`. The tests may only need to be reviewed or expanded if additional edge cases are discovered.

### Plan

1. Inspect the file-processing loop in `TechDetector.execute()` to identify where file paths are counted by extension.
2. Add a path-filtering check that excludes files located inside known vendored or generated directories such as `node_modules/` and `build/`.
3. Ensure the filtering works for relative paths and does not exclude normal source files whose filenames merely contain similar text.
4. Run the two failing unit tests to verify that Python becomes the primary language after excluded paths are removed.
5. Run the complete `tests/unit/test_tech_detector.py` test file to confirm the change does not break existing language or framework detection behavior.

### Inputs & outputs

The input is a dictionary containing a list of repository file paths, for example:

```python
{
    "files": [
        "src/main.py",
        "node_modules/package/index.js",
        "build/bundle.js"
    ]
}