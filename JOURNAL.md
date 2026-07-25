# Module 3 Journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/119

**Issue title:** Add inline docstrings to all public methods in `core/services/`

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
The service layer in `core/services/` was missing proper documentation - most functions had at most a one-line description, with no information about what parameters they accept, what they return, or when they raise an exception. Issue #119 asks for full Google-style docstrings (description, Args, Returns, and Raises) on every public method across `profile_service.py`, `review_service.py`, and `notification_service.py`. A successful fix means someone reading these files can understand how to call each function and what to expect back without tracing through the implementation. One catch I ran into: `notification_service.py` is listed in the issue, but that file doesn't exist anywhere in the repo - only `profile_service.py` and `review_service.py` are present under `core/services/`, so my actual scope was those two files.

**Is this right for me? — checklist reasoning:**
This felt like a reasonable scope for a first contribution, though in practice it turned out to be easier than expected - despite the tier-2 label, the work was mechanical documentation rather than anything requiring deep architectural changes. The main scope surprise was discovering that `notification_service.py`, one of the three files the issue names, doesn't exist in the codebase at all, so I scoped my work to the two files that do exist and noted the discrepancy here rather than guessing at what a nonexistent file should contain.

**Branch name:** docs/119-service-docstrings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vzan2012/pathreview/commit/c02d7eaac82b359315a463dfba7f592f3f62bdbb

**Reproduction summary:**
I confirmed the gap by running `git show 10d3713:core/services/profile_service.py` to view the original functions before my fix — each one had only a one-line docstring (e.g. `create_profile` just said `"""Create a new profile for a user."""`) with no Args, Returns, or Raises sections, matching exactly what issue #119 describes.

**PLAN.md link:** https://github.com/vzan2012/pathreview/blob/docs/119-service-docstrings/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The actual docstring fix — and the type-annotation fixes needed to get the mypy pre-commit hook passing — were already completed and committed back in Week 7, ahead of this week's plan-then-build pacing. `PLAN.md` below documents the approach I actually followed rather than a forward-looking plan. No PR has been opened yet; that's a Week 9 step per the module schedule.
