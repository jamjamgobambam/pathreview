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

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the issue #150 fix from `PLAN.md`. The tech detector now filters ignored directories by normalized path parts, so root-relative and nested paths such as `node_modules/lib/index.js` and `build/bundle.js` do not affect language detection. Added/updated unit coverage in `tests/unit/test_tech_detector.py`, including a regression test for vendored and build-output JavaScript files not dominating a Python project.

**Next steps:**
Open a pull request from `fix/150-exclude-vendored-build-files` to `ascherj/pathreview:main`, paste the completed PR description, request peer or mentor feedback, and update this journal with the final PR link.

**Blockers:**
`make` is not installed in this PowerShell environment, so I could not run the literal `make check` or `make test-unit` commands here. Running the equivalent checks directly showed pre-existing repo-wide failures outside this issue's files: `ruff check .` reports 173 unrelated lint issues, and `python -m pytest tests/unit -v -m unit` reports 50 failed, 348 passed, and 31 errors. The issue-specific checks pass.

---

### Check-in 2 (end of week)

**PR link:** TODO - add the GitHub pull request link after opening the PR.

**What you built:**
The fix normalizes repository paths, splits them into directory/file parts, and skips files when any path part matches ignored dependency, vendor, build, cache, virtualenv, or git metadata directories. It also chooses the primary language from counted real source/config signals instead of a sorted set, which prevents ignored generated JavaScript from skewing the result.

**Tests added or updated:**
Updated `tests/unit/test_tech_detector.py`. The new regression coverage verifies that JavaScript files under `node_modules` and `build` are ignored and that Python remains the only detected language for the reproduction case.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Direct validation completed because `make` is unavailable in this shell:

- [x] `ruff check agent/tools/tech_detector.py tests/unit/test_tech_detector.py` passes
- [x] `python -m pytest tests/unit/test_tech_detector.py -v -m unit` passes: 28 passed
- [ ] Repo-wide `ruff check .` passes: currently fails with pre-existing unrelated lint issues
- [ ] Repo-wide `python -m pytest tests/unit -v -m unit` passes: currently 50 failed, 348 passed, 31 errors in unrelated areas

**Draft PR feedback received from:** TODO - add reviewer name/handle, or `none` if no peer or mentor feedback is received before submission.
