## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/119

**Issue title:** Add inline docstrings to all public methods in core/services/

**Tier:** [ ] Tier 1 [X] Tier 2 [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is set in the service layer under core/services/, where the functions that mediate the API routes and database models are. Many of the functions are inconsistently documented, with the public functions either carrying only one-line docstrings (or none) without any structured account of their parameters, return values or failure modes. Without strong docstrings, the service layer is made more difficult to tell what the db expects, when a function returns "None" versus raising, or which operations can throw after a rollback. The fix, and what would be considered "done" is then to give each of the public functions a complete Google-styled docstring, a description including the Args taken, possible Returns, and Raises that reflect each function's actual behavior. A successful outcome is that the modules present in the directory read as self-documenting, with the Raises sections honestly distinguishing functions that genuinely raise from pure reads that only surface underlying database errors.

**Branch name:** 'origin/issue-119-missing-docstrings-in-services-directory'

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**CheckList responses**:

- Can I find the relevant code?
  - The issue lists the files in question. Profile_service.py, review_service.py.
  - Only issue is that I couldn't find anything for the notification_service.py
- Blockers/dependencies:
  - Despite not having found the notification_service.py, I would write it off as something that I can put aside, as I did a check of any files referencing the module and couldn't find anything. Most likely that whatever issue involving notification services were resolved indirectly in a different PR.
- Tier realistic:
  - Is tier-2, with an estimated effortof 4-6 hours. I would need to understand how the service modules work and what depends on these modules to write the most accurate docstring descriptions.
- Realistic for my schedule?
  - Yes. I can reserve Thursdays and Fridays and the Weekends.
- How does it align with my skill level?
  - I am an intermediate level software engineer who has had experience adding onto pre-existing codebases, but I've not done much on the documentation/explanation process, where I need to let the reviewer know the why or what. The main fix would require me to find the right files, understand where it's referenced and depended on, and that helps me understand the bigger picture.

viperkill420 user id: d20820e3-cc76-46a3-8016-21a6e242a5c1

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kylipoo/pathreview/commit/49f3ad61f38857859b7580b431317a5cc0f4cd44

**Reproduction summary:**
I opened core/services/profile_service.py and review_service.py and could confirm that as the original issue stated, that every public function is documented with only a one-line summary — no structured account of its parameters, return values, or failure conditions. To confirm the undocumented behaviors, I exercised the API and called get_profile directly, observing that: reads collapse "not found" and "not owned" into a silent None; create_profile can raise on commit without rolling back; and delete_profile re-raises after a rollback.

**PLAN.md link:** https://github.com/kylipoo/pathreview/blob/docs/119-missing-docstrings-in-services-directory/PLAN.md

**Walkthrough video (recommended):** (Not much to share here, is an issue of documentation).

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

- I have written my docstrings for the profile_service.py, checking in with Claude's analysis of the codebase and comparing it with my own.
  - Explains the params, what the function does with the params, and return values.
  - I brought up "Raise" conditions where an error may happen.
- Created a pytest for profile_service for my own test purposes to verify docstring is correct.

**Next steps:**

- I plan on continuing to working on the review_service.py docstrings.
- I see that there is already a test_review_service.py function, I may run it, see if there is anything I will need to add to make it run properly.

**Blockers:**

- Claude went down today 11/29, so it may take a bit of time to get back on track.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
