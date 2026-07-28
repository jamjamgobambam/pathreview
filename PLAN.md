# PathReview Issue #150 Plan

## Solution plan

**Issue:** [Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

`TechDetector` receives a list of repository-relative file paths and filters
out files that should not affect technology detection. The current
`_should_skip_file()` implementation searches for strings such as
`/node_modules/` and `/build/`. This works when the ignored directory appears
below another directory, such as `frontend/node_modules/package/index.js`, but
it does not work when the ignored directory is at the root of the repository,
such as `node_modules/package/index.js`.

Because those JavaScript files remain in the filtered file list, JavaScript is
added to the detected languages. The detector then selects JavaScript as the
primary language instead of Python. The expected behavior is for dependency,
vendor, virtual-environment, cache, and generated-output directories to be
excluded regardless of whether they appear at the repository root or inside
another directory.

### Map

The main files involved are:

- `agent/tools/tech_detector.py`
  - `TechDetector._detect_tech()`
  - `TechDetector._should_skip_file()`
- `tests/unit/test_tech_detector.py`
  - `test_node_modules_excluded`
  - `test_vendor_files_excluded`
  - `test_build_directory_excluded`
  - Additional regression tests for nested paths and Windows path separators

`_detect_tech()` calls `_should_skip_file()` before inspecting file extensions
and configuration filenames. The fix should therefore remain focused on the
path-filtering stage.

### Plan

1. Normalize each incoming file path so both forward slashes and Windows
   backslashes can be handled consistently.
2. Split the normalized path into directory components rather than searching
   for skip-directory names using leading-slash substrings.
3. Mark a file as skipped when one of its directory components exactly matches
   a known ignored directory such as `node_modules`, `vendor`, `dist`, `build`,
   `.git`, `__pycache__`, `.venv`, or `venv`.
4. Strengthen the existing unit tests so they verify that languages found only
   in ignored directories are absent from `all_languages`, not merely that
   Python happens to be selected as the primary language.
5. Add regression coverage for root-level ignored directories, nested ignored
   directories, Windows-style backslash paths, and similarly named legitimate
   directories. Run the targeted test file and then the complete unit test
   suite.

### Inputs & outputs

The input is a list of repository-relative file paths supplied through:

```python
TechDetector.execute({"files": files})

Example input:

[
    "main.py",
    "core/app.py",
    "node_modules/lib/index.js",
    "build/bundle.js",
]

Before the fix, JavaScript files inside ignored directories may remain in the
analysis and produce:

{
    "primary_language": "JavaScript",
    "all_languages": ["JavaScript", "Python"],
    "frameworks": [],
}

After the fix, the ignored JavaScript files should not affect detection:

{
    "primary_language": "Python",
    "all_languages": ["Python"],
    "frameworks": [],
}

The public output structure of TechDetector should remain unchanged.

Risks & unknowns
- A broad substring check could incorrectly skip legitimate paths such as
src/rebuild/parser.py because the directory name contains build. The implementation should compare complete directory components instead.
- Windows paths may use backslashes while repository APIs commonly return forward slashes. Path normalization must support both.
- Configuration files inside excluded directories must also be filtered so they do not introduce frameworks such as Node.js.
- If every supplied file is excluded, the detector should continue returning Unknown instead of raising an exception.
- The current primary-language selection behavior may have unrelated issues. This fix should remain limited to Issue #150 unless testing proves a broader
change is required.


Edge cases

The implementation and tests should cover:

- Root-level dependency paths:
    node_modules/package/index.js
- Nested dependency paths:
    frontend/node_modules/package/index.js
- Root-level build output:
    build/bundle.js
    dist/app.js
- Nested build output:
    frontend/build/bundle.js
- Windows-style separators:
    frontend\node_modules\package\index.js
- Virtual environments and caches:
    .venv/Lib/site-packages/library.py
    src/__pycache__/module.pyc
- Legitimate similarly named directories that should not be skipped:
    src/rebuild/parser.py
    src/vendor_tools/helper.py
- Configuration files inside ignored directories:
    node_modules/package/package.json
- An input where all files are excluded, which should return an unknown language without crashing.