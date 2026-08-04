## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/119)]

**Issue title:** [Add inline docstrings to all public methods in core/services/ # 119]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
All service files under core/services module don't have docstrings. Without docstrings, developers that are new to this codebase will have to read into the functions within `profile_service.py` and `review_service.py` to understand what they do. Adding docstrings into these files will help developers who just want to use these functions without reading the underlying logic

**Branch name:** [docs/119-add-inline-docstrings]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Scope and Time:**
- There are no blockers that need to be resolved first before this issue

- I have 2 weeks before end of module 9 to add docstrings to all functions within `profile_service.py` and `review_service.py` so I'm confident I can complete this task.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vanthuynh/pathreview-colab/commit/7fd95aa5658e03bdd66c04f17fbd4466da2f6034

**Reproduction summary:**

I reread the issue and confirmed that neither `services/profile_service.py` nor `services/review_service.py` have docstrings for their functions

**PLAN.md link:** https://github.com/vanthuynh/pathreview-colab/blob/docs/119-add-inline-docstrings/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**

This issue is straightforward since I made time to clearly understand the issue and read the code base carefully. Also because I have completed week 7 objectives, which helped me tremendously before going to reproduction and solution planning step


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I added docstrings with Google-style formatting to 4 functions in `profile_service.py` and 8 functions in `review_service.py`

**Next steps:**
I need to ensure that my commit messages follow the correct format. I also need to run code-quality check with `make check`, run test with `make test-unit`

**Blockers:**
None

## PR Drafts
## Summary
From this PR, I added the missing docstrings to all public functions within `core/services/profile_service.py` and `core/services/review_service.py` where I comprehensively document each function' arguments, return values, and any raised exceptions. These documentation updates must be made without altering the existing runtime behavior.

## Issue
Closes #119 

## Changes

- I added docstrings with Google-style formatting to 4 functions in `profile_service.py` and 8 functions in `review_service.py`
- Added JOURNAL.md with the issue selection, solution planning, and solution building with validation result
- Added PLAN.md documenting the problem investigation, plans, risks, and edge cases.


## Testing
<!-- How did you verify your changes? -->
- [ ] Unit tests pass (`make test-unit`)
   - Running `make test-unit` resulted in 53 failed test cases and 375 passed test cases. 
   - This PR doesn't make any changes that affected existing test cases
- [ ] Integration tests pass (`make test-integration`)
   - No integration test ran
   - This PR doesn't make any changes that affected existing integration test
- [ ] Linter passes (`make lint`)
   - Running `make lint` resulted in 180 errors in the repository
- [ ] Type checker passes (`make typecheck`)
   - Running `make typecheck` resulted in 5 errors in 4 files
   - This PR doesn't make any changes that affected existing test cases
- [ ] New/updated tests cover the changes

## Screenshots / Demo
No demo video necessary for this issue

## Notes for Reviewers
<!-- Anything the reviewer should pay particular attention to -->
- This issue references `core/services/notification_service.py`, but that file does not exist on the current upstream/main. 
- This PR only add docstrings to all public functions in `profile_service.py` and `review_service.py`.
- Since this PR only added docstrings to public functions, no change in this PR affected pre-existing validation test or any linting errors.