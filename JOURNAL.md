# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `TechDetector` agent tool analyzes a repo's file list to guess its primary
programming language, but it doesn't actually filter out vendored or
build-output paths before counting file extensions. A repo with only 2 Python
source files and several bundled JavaScript files under `node_modules/` or
`build/` gets reported as primarily JavaScript instead of Python, which
defeats the point of the detector — it should reflect what the author wrote,
not what got bundled or vendored into the repo. The affected code lives in
`agent/tools/tech_detector.py`, specifically the `_should_skip_file` method
that's supposed to exclude these paths. A successful fix makes the detector
correctly ignore vendored/build files so the reported primary language
matches the repo's actual source composition.

**Branch name:** fix/150-tech-detector-vendored-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
