# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview’s technology detector is supposed to ignore dependency and generated-output directories when determining a repository’s programming languages. However, its current skip patterns contain leading slashes, so root-level paths such as `node_modules/package/index.js` and `build/bundle.js` are not excluded. As a result, vendored or generated JavaScript files can affect language detection and cause the repository’s primary language to be reported incorrectly. A successful fix will make the filtering logic work for both root-level and nested directories while passing the existing unit tests.

**Selection notes — “Is this issue right for me?” checklist:**

- The expected behavior and current failure are clearly explained.
- The issue includes a reproducible example and identifies relevant failing tests.
- The likely scope is limited to `agent/tools/tech_detector.py` and `tests/unit/test_tech_detector.py`.
- The issue does not require a database migration, external API integration, or major frontend changes.
- I have experience with Python, backend development, file-processing logic, and unit testing.
- I understand the likely cause: root-level paths do not contain the leading slash used by the existing skip patterns.
- I will verify root-level paths, nested paths, and path separators without changing unrelated detection behavior.
- This Tier 1 issue has a realistic scope for my first contribution to this repository.

**Branch name:** `fix/150-ignore-vendored-build-files`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger