## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/119

**Issue title:** Add inline docstrings to all public methods in `core/services/`

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The public service functions in `core/services/` have docstrings, but they do not consistently document their parameters and return values. This makes it harder for contributors to understand how to call the profile and review service functions. The fix updates the eight public functions in `profile_service.py` and `review_service.py` with consistent Google-style `Args:` and `Returns:` sections, plus `Raises:` where applicable. A successful change improves documentation without changing application behavior.

**Branch name:** `docs/119-service-docstrings`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
This Tier 2 issue has a clear, manageable scope and matches my familiarity with Python service functions, type annotations, and documentation. The expected changes can be verified by reviewing the function signatures, generated docstrings, and repository validation results. The issue references `core/services/notification_service.py`, but I verified that this file does not exist in the latest `upstream/main`. Therefore, the implementation covers the eight public functions in `profile_service.py` and `review_service.py` without creating an unrelated service file.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [docs: document issue reproduction and solution plan](https://github.com/thanh-cnguyen/pathreview/commit/c95a7b8deaf17ed0153b211a330732afec292228)

**Reproduction summary:**
I reproduced the documentation gap by comparing the public service functions on `upstream/main` with their signatures. The eight public functions in `profile_service.py` and `review_service.py` did not consistently document their parameters, return values, and applicable exceptions.

**PLAN.md link:**
https://github.com/thanh-cnguyen/pathreview/blob/docs/119-service-docstrings/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**
The implementation was completed before this planning milestone because I initially understood the previous milestone to include implementing the issue. The plan below documents the investigation and implementation approach followed.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the planned documentation updates for the eight public functions in
`profile_service.py` and `review_service.py`. I also added the minimal type
annotations needed for the modified functions and completed all implementation
sub-tasks listed in `PLAN.md`.

**Next steps:**
Run the repository validation commands, document any pre-existing failures,
self-review the changes, and finalize the pull request for submission.

**Blockers:**
The repository-wide unit-test, lint, and type-check commands report existing
errors outside this PR’s documentation-focused scope.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/thanh-cnguyen/pathreview/pull/1

**Branch:** `docs/119-service-docstrings`

**What you built:**
Added consistent Google-style docstrings to the eight public functions in
`profile_service.py` and `review_service.py`. The docstrings now document
arguments, return values, and applicable exceptions without changing application
behavior. Minimal type annotations were also added for clarity.

**Tests added or updated:**
None. This PR updates documentation and type annotations without changing
application behavior, so no test files were added or modified. The applicable
validation commands and their results are documented in the PR description.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none
