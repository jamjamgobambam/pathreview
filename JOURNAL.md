## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The tech detector currently tries to exclude generated and dependency directories, but its path checks miss common relative paths such as `node_modules/lib/index.js` and `build/bundle.js`. This affects `agent/tools/tech_detector.py`, where repository file paths are converted into detected languages and a primary language. The bug matters because vendored or bundled JavaScript can drown out the user's real source files, causing PathReview to misidentify a mostly Python project as JavaScript. The fix should normalize file paths, skip ignored directory names wherever they appear in the path, and choose the primary language from real source-file counts.

**Selection notes:**
This is a good first issue because it is isolated to one agent tool and has a clear reproduction example in the issue description. The related tests live in `tests/unit/test_tech_detector.py`, so the validation path is narrow and does not require the full app stack. The scope is small enough for Week 7/8, but still meaningful because it improves the accuracy of repository analysis.

**Branch name:** fix/150-exclude-vendored-build-files

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/JohnsonGNEP/pathreview/commit/96a97240a534624b6569ce0fa9ada2db8cbc91f8

**Reproduction summary:**
I reproduced the issue with a file list containing real Python files plus generated JavaScript paths like `node_modules/lib/index.js` and `build/bundle.js`. The original path filter only matched slash-wrapped directory patterns, so root-relative ignored paths were not skipped and could skew detected languages away from the user's real source files.

**PLAN.md link:** https://github.com/JohnsonGNEP/pathreview/blob/fix/150-exclude-vendored-build-files/PLAN.md

**Loom walkthrough:** TODO - add Loom link after recording the <=2 minute walkthrough.

**Blockers or open questions:**
No code blockers. The remaining course deliverable is recording and adding the Loom walkthrough link.
