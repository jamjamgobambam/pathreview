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

- I have written my docstrings for the profile_service.py, checking in with Claude's analysis of the codebase and comparing it with my own.
  - Explains the params, what the function does with the params, and return values.
  - I brought up "Raise" conditions where an error may happen.
- Created a pytest for profile_service for my own test purposes to verify docstring is correct.

**Next steps:**

- I plan on continuing to working on the review_service.py docstrings.
- I see that there is already a test_review_service.py function, I may run it, see if there is anything I will need to add to make it run properly.

**Blockers:**

- Claude went down today 7/29, so it may take a bit of time to get back on track.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/397

**Branch:** docs/119-missing-docstrings-in-services-directory

**What you built:**
I added docstrings to the 4 public functions for review_service.py (create_review, get_review, list_reviews, process_review). I covered the arguments, return values, raise conditions, plus the caveats the signatures don't show: : create_review accepts a user_id it never checks, get_review can't distinguish "no such review" from "not yours", and process_review never raises at all because it converts every exception into status="failed". While documenting process_review I found that it assigns a list to review.sections while the model declared it Mapped[dict | None], so I corrected the model to list[dict] | None to match both the service and the API schema. I also annotated the db parameters as AsyncSession, which the pre-commit mypy hook needed to pass on this file.

**Tests added or updated:**
(This is additional to what I built). I added tests/unit/test_service_docstring_claims.py with 15 unit tests, one per documented claim across both service modules. These include asserting that update_profile leaves None fields at their current value, that delete_profile rolls back before re-raising, that get_review enforces ownership inside the SQL rather than in Python, that list_reviews reports the total across all pages, and that process_review never raises and never records an error_message. The tests have been verified to not be vacuous by temporarily breaking the partial-update behavior and confirming the corresponding test failed.

**Self-review confirmation:** [X] make check passes [X] make test-unit passes

The test_service_docstring_claims tests all successfully passed. Any of the 180 errors in make check were pre-existing, the 53 errors from make test-unit are also pre-existing. Though my test file added 15 more (successful) tests.

**Draft PR feedback received from:** Shawn Blackman (GitHub handle is: sh4wnbk)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes [ ] No — still awaiting review

**Summary of feedback:**

Reviewed twice by Shawn Blackman.

First pass: One blocking mismatch. My summary claimed that Google style docstrings would be applied to eight public functions across both service files, but as this was a first check milestone, review_service.py still had its incomplete one-line docstrings. As for what I had completed by that milestone, Shawn verified each profile_service.py docstring against its body, and he found no overstatements. delete_profile correctly documents re-raising after rollback and the code does exactly that; the other three are read-only or non-raising and don't claim otherwise; and update_profile's note about leaving None fields unchanged matches the conditional guards in the body.

Second pass: With review_service.py's four public functions now given the proper docstring formats carrying Args/Returns/Raises, the eight public functions across two service files claim matches the diff. Shawn spot checked the raise claims and called out create_review documenting IntegrityError on a bad profile_id as exactly right — the commit isn't wrapped and reviews.profile_id is a non-null FK, so the error genuinely reaches the caller. That's a database-layer raise with no explicit raise in the body, easy to get wrong in either direction. He also endorsed documenting that user_id is accepted but unused with the ownership check left to the caller, as surfacing an unenforced assumption rather than hiding it.

Also on the second pass, I added a test file that verified the function behavior matched as docstrings claimed. Shawn noted they exercise real behavior rather than mocking it away.

**How you responded:**
I pushed the missing review_service.py docstrings so the eight-function claim matched the diff, and updated the PR description to name the core/models/review.py change and the type annotations rather than leaving them as undisclosed extras. The tautological assertion Shawn flagged is at tests/unit/test_review_service.py:121, a file this PR doesn't modify — my tests are in test_service_docstring_claims.py — so I left it alone and noted it as a separate issue, along with the AsyncMock problem in that same file that causes its 13 failures.

### Reflection

**What was harder than you expected?**
One thing that surprised me was that even though the assignment was a simple documentation, it wasn't just in the scope of those two service files. I found personally, that by running the application and playing with its functionality and checking for all references to the service file functions, that it helped give me a better understanding on what I should write for the behavior of the functions. For example, documenting process_review meant reading api/routes/reviews.py to learn it's registered as a background task, and reading core/models/review.py to check what sections actually holds — which is where I found the model declared it Mapped[dict | None] while the service assigns a list and the API schema declares a list. I couldn't have written an honest docstring without leaving the file, and the bug only showed up because I did.

**What did you learn about working in a large codebase?**
That "the tests pass" and "the linter passes" aren't binary facts about my work. I have to know the repo's baseline first. main here already has 53 unit-test failures and 180 lint errors, so my first instinct that I'd broken something was wrong, and I only knew that because I measured before starting and compared after. I also learned the tooling isn't one thing: the pre-commit mypy hook runs in its own environment without SQLAlchemy installed, so it gave a different answer than mypy in my venv on the identical file. And make check, which CONTRIBUTING.md tells contributors to run, executes black . with no --check flag — it would have reformatted 50 files into my PR if I'd run it and made it very confusing which changes were meant to address the issues itself, and then have a feedback loop where future developers handling issues would have no idea what they're looking at.

**How did AI tools help — and where did they fall short?**

AI assistance was very good at helping explain what this codebase did, what the service files did, and adding a test file. I feel where I needed to go beyond what AI could give me was paraphrasing the service files in a way that newcomers could understand.

**What would you do differently if you started over?**
I made a lot of commits fixing typos and rewording the PR description, which made the history noisy and hard to read. I'd draft the description and journal entries somewhere else first and commit them once. I'd also check git status more carefully — I spent a while confused by a mypy hook that kept failing on errors I'd already fixed, because my fixes were unstaged and pre-commit only checks what's staged.

**What are you most proud of from this module?**
I am proud of how I went above and beyond the original requirements and how I interpreted them, making my changes verifiable even if not programmatic. The tests in test_service_docstring_claims.py pin each claim to the behavior it describes, so if someone later makes update_profile clear a None field, a test fails and names the docstring it contradicts. I also confirmed the tests weren't vacuous by deliberately breaking that guard and watching the right test fail — I'd rather know my tests work than assume it.
