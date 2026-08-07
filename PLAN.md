## Solution plan

**Issue:** [Tech detector counts vendored and build-output files, skewing language detection](https://github.com/ascherj/pathreview/issues/150)

### Understand

The expected fix isolates primary language identification by actively filtering `node_modules/` and `build/` directories, preventing bundled assets (e.g., vendored JavaScript) from eclipsing actual source code (e.g., Python). Initial logic and parameters surrounding the exclusion patterns in `tech_detector.py` (lines 153–161) are validated.

### Map

Target architecture and testing surface are validated.

1. `tech_detector.py` (`tech_detector._should_skip_file`)
2. `test_tech_detector.py`

### Plan

1. Integrate exact path-matching exclusions for `node_modules/` and `build/` within the target configuration.
2. Execute standard processing and validate regressions via `test_tech_detector.py`.

### Inputs & outputs

**Input:** A file path (string).
**Output:** A boolean indicating whether the file should be skipped, successfully rejecting paths containing vendored or build directories.

### Risks & unknowns

Applying broad static exclusion lists risks false negatives, potentially skipping legitimate source repositories that happen to utilize non-standard naming conventions overlapping with build artifacts. Relying solely on static directory names is a blunt instrument; a more robust future iteration might contextually evaluate project architecture or utilize `.gitignore` propagation.

### Edge cases

The system must gracefully handle empty path inputs, malformed strings, and accurately differentiate between root-level versus nested `node_modules/` and `build/` directories without throwing exceptions.