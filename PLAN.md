## Solution plan

**Issue:** tech_detector.py does not exclude node_modules/ or build/ paths (https://github.com/ascherj/pathreview/issues/150)

### Understand
The technology stack detector uses a list of skip patterns (e.g., `"/node_modules/"`, `"/build/"`) to filter out vendored or built files. When relative file paths are supplied without a leading slash (like `"node_modules/..."`), the substring checks fail because the leading slash is missing. Additionally, Windows backslashes (`\`) in paths prevent matching with forward slash patterns.

### Map
* [tech_detector.py](file:///c:/Users/adith/Codepath/pathreview/agent/tools/tech_detector.py) (specifically `TechDetector._should_skip_file`)

### Plan
1. Normalize path separators in the file path by replacing `\` with `/`.
2. Ensure the file path starts with a leading `/` so that relative paths match the skip patterns (e.g., `/node_modules/`).
3. Run the unit test suite (`pytest tests/unit/test_tech_detector.py`) to verify the fix.

### Inputs & outputs
* **Input:** A file path string (e.g., `"node_modules/lib/index.js"` or `"node_modules\lib\index.js"`).
* **Output:** Returns `True` if the path contains any of the skip patterns (excluding it from analysis), `False` otherwise.

### Risks & unknowns
* **Risks:** Extremely low, as the change is self-contained within the helper method `_should_skip_file` used only for filtering file lists.

### Edge cases
* Windows paths with backslashes (`\`) are normalized to forward slashes.
* Paths beginning directly with skipped folder names (e.g. `"node_modules/..."`) are correctly prefixed with `/` for pattern matching.