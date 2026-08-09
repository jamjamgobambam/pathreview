# Solution plan

**Issue:** [Tech detector counts vendored and build-output files, skewing language detection — #150](https://github.com/ascherj/pathreview/issues/150)

**Working branch:** `fix/150-ignore-vendored-build-output`

### Understand

The technology detector receives repository file paths and passes them through `TechDetector._should_skip_file()` before detecting languages and frameworks. The current skip patterns in `agent/tools/tech_detector.py` include strings such as `"/node_modules/"` and `"/build/"`. Those patterns work when an ignored directory appears after another path segment, such as `"frontend/node_modules/package/index.js"`, but they do not match root-relative paths such as `"node_modules/package/index.js"` or `"build/bundle.js"` because those paths have no leading slash.

As a result, JavaScript files from third-party dependencies and generated build output remain in `filtered_files`. Their `.js` extensions are then treated as repository source code, which adds JavaScript to the detected languages and causes the two issue-specific tests to report JavaScript instead of the expected Python.

**Expected behavior:** Files inside ignored directories should not influence `primary_language`, `all_languages`, or `frameworks`, whether the ignored directory is at the repository root or nested inside another directory.

**Actual behavior:** Root-level `node_modules/` and `build/` paths are not skipped, so their files influence technology detection.

**Decision and reason:** I will fix directory recognition inside `_should_skip_file()` instead of adding special cases inside the language-detection loops. Filtering is already this method's responsibility, and correcting it once protects both extension-based language detection and configuration-file detection.

**Scope decision and reason:** I will not redesign how `_detect_tech()` selects the primary language. Although that method currently stores languages in a set and selects the first sorted value, issue #150 and its acceptance tests concern ignored paths. Changing primary-language ranking would expand the scope and could alter unrelated behavior.

### Map

I expect to modify these files:

1. **`agent/tools/tech_detector.py`**
   - Function: `TechDetector._should_skip_file()`
   - Role: Normalize incoming file paths and determine whether any directory component is in the existing ignored-directory list.
   - Reason: This is the source of the root-level matching failure and the single filtering point used before both language and framework detection.

2. **`tests/unit/test_tech_detector.py`**
   - Tests: `test_node_modules_excluded` and `test_build_directory_excluded`
   - Additional coverage: nested ignored directories, Windows-style separators, and similarly named directories that should not be ignored.
   - Reason: The existing failing tests prove the reported bug. Additional focused cases will prevent a partial fix that works only for one path format or skips valid directories accidentally.

No frontend, API, database, or configuration files should need changes because the defect is contained within the detector's file-path filtering logic.

### Plan

1. **Preserve the reproduced failure as the baseline.**
   - Re-run the two issue-specific tests before implementation and confirm that both fail with JavaScript returned instead of Python.
   - Reason: This provides a clear before-and-after comparison and confirms that the later passing result is caused by the fix.

2. **Replace slash-dependent substring matching with directory-component matching.**
   - Normalize backslashes to forward slashes so paths from Windows and Unix-like systems have one comparable format.
   - Split the normalized path into components and compare directory components with the existing ignored directory names, including `node_modules`, `vendor`, `dist`, `build`, `.git`, `__pycache__`, `.venv`, and `venv`.
   - Reason: Component matching detects ignored directories at both root and nested positions. It also avoids false matches in legitimate names such as `build_tools` or `node_modules_backup`.

3. **Strengthen the focused unit tests.**
   - Keep the existing root-level `node_modules/` and `build/` reproduction cases.
   - Assert that ignored JavaScript files do not appear in `all_languages`, not only that `primary_language` is Python.
   - Add representative nested paths and Windows-style backslash paths.
   - Add a similarly named directory case to prove that only exact directory components are ignored.
   - Reason: Testing both the positive and negative boundaries verifies the intended behavior without relying only on the current primary-language selection implementation.

4. **Run targeted and regression tests.**
   - First run the two issue-specific tests for fast feedback.
   - Then run the complete `tests/unit/test_tech_detector.py` file.
   - Finally run the repository's documented broader test command if the focused suite passes.
   - Reason: The targeted tests verify issue #150 directly, while the wider tests check that existing language and framework detection behavior was not broken.

5. **Review the final diff before committing the implementation.**
   - Confirm that changes are limited to the detector and its unit tests and that no generated, dependency, or environment files are included.
   - Reason: Keeping the commit focused makes the fix easier to review and prevents unrelated local setup changes from entering the pull request.

### Inputs & outputs

**Input:** `TechDetector.execute()` continues to accept a dictionary containing `"files": list[str]`. Each string may be a root-relative, nested, absolute, Unix-style, or Windows-style file path.

**Output:** The public `ToolResult` structure remains unchanged:

- `primary_language`: the selected language or `"Unknown"`
- `all_languages`: sorted detected languages
- `frameworks`: sorted detected frameworks

The intended change is only which paths are allowed to contribute to those values.

| Example input path | Intended filtering result | Reason |
|---|---|---|
| `node_modules/pkg/index.js` | Skip | `node_modules` is an ignored root directory |
| `frontend/node_modules/pkg/index.js` | Skip | An ignored directory may be nested |
| `build/bundle.js` | Skip | Generated build output should not count |
| `frontend\build\bundle.js` | Skip | Windows separators should behave consistently |
| `src/build_tools/helper.js` | Keep | `build_tools` is not the exact ignored name `build` |
| `src/main.py` | Keep | It is repository source code outside an ignored directory |

**Decision and reason:** The method signatures and returned data structure will not change because callers should receive the same API; only the accuracy of the filtered input should improve.

### Risks & unknowns

- **Cross-platform separators:** Git file lists often use `/`, but local or external callers may supply `\`. The implementation must normalize both formats before matching.
- **False-positive directory names:** A broad substring check could incorrectly skip paths such as `src/build_tools/` or `node_modules_backup/`. Exact component comparison is required.
- **Root, nested, and absolute paths:** The solution must behave consistently for `build/file.js`, `app/build/file.js`, and `/workspace/app/build/file.js`.
- **Existing ignored directories:** The current list also includes `vendor`, `dist`, `.git`, `__pycache__`, `.venv`, and `venv`. The new matching logic should preserve these exclusions and make their root-level behavior consistent.
- **Framework detection:** Ignored directories can contain files such as `package.json`. Because `filtered_files` feeds both detector loops, tests should confirm the fix prevents ignored configuration files from adding frameworks as well as languages if this behavior is covered by the existing design.
- **Primary-language calculation:** `_detect_tech()` currently uses a set of detected languages rather than counting files, even though the issue description discusses skewed counts. This is related code but is not required to make the supplied issue tests pass. I will treat it as a separate concern unless maintainers clarify that issue #150 also requires changing the ranking algorithm.
- **Input validation:** The declared input is a list of path strings. Handling non-string values is outside the current issue unless testing reveals that such values are part of the supported contract.

### Edge cases

The fix should handle these cases gracefully:

- The ignored directory is the first component of a relative path.
- The ignored directory appears several levels inside a path.
- The path uses Windows backslashes, Unix forward slashes, or a mixture of both.
- The path is absolute rather than repository-relative.
- A valid directory merely contains an ignored word, such as `build_tools`, `rebuild`, or `node_modules_backup`.
- Ignored directories contain recognized source extensions or configuration filenames.
- All supplied files are ignored; the detector should return `"Unknown"` with empty language and framework lists.
- The file list is empty; existing `"Unknown"` behavior should remain unchanged.
- Normal source files outside ignored directories continue to be detected.
- Existing ignored directories such as `vendor`, `dist`, `.git`, `__pycache__`, `.venv`, and `venv` continue to work at root and nested levels.

This plan is a living document and may be updated in Week 9 if implementation or test results reveal an additional repository requirement.
