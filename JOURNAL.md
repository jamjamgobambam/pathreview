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


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/762

**Branch:** `docs/119-add-inline-docstrings`

**What you built:**
I added docstrings with Google-style formatting to 4 functions in `profile_service.py` and 8 functions in `review_service.py`

**Tests added or updated:**
I did not add any test files since this issue only covers updating docstrings for existing functions.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
N/A

**How you responded:**


---

### Reflection

**What was harder than you expected?**
- The first thing that caused me some troubles was that `mypy` prevented me from making commits when the code base still have incompatible types in variable assignments

- Due to the nature of the codebase, reading and understanding the functions from the `\service` module alone are complicated and required a good amount of time for me to understand their objective and behaviors.

**What did you learn about working in a large codebase?**

- For my own projects, I usually don't build this much tests, nor have any other `.md` files for contributing rules, architecture, and setup instructions. From this project, I learned about the necessity of all of these steps and will apply them to my future projects.

**How did AI tools help — and where did they fall short?**
- AI helped me reread and evaluate my docstrings after I have read the `\service` module and fill in the docstrings myself. Since this issue is mainly understanding the functions and their behavorial, Claud helps me very well with putting in the correct docstrings and didn't require much context the span multiple parts of the codebase.


**What would you do differently if you started over?**
- If I started over, I'd choose a different issue that may require more codebase reading and more additional tests to find out the bug

**What are you most proud of from this module?**
- I am most proud of applying what I have learned from this propram. This mean I was able to apply contributing best practice such as naming branch, commits format, and pull request practice for open-source projects. I also was able to leverage AI in helping me reevaluate my code/dosctrings before I'm confident that my solution for the issue is good before making a pull request.