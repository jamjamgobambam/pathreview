## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

The issue asks to implement a system where users are able to share a read-only view of their review summary. The link should be accessible without the need to login and expires after 30 days. Even though `frontend/src/services/shareService.ts ` does not exist, there are exisiting APIs I can use to help build the frontend-backend connection to populate the page. A share button exists, but the link generation, public view and expiration needs to be implemented. A successful fix would have the previously stated features implemented.

**Branch name:** feat/101-review-copy-link

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

** Is this Issue Right for Me?*

*Part 1*: The issue asks to implement a feature where the user can share the results of pathreview. I need to implement methods to handle link generation, expiration, and privacy. Additionally, I need to ensure there are API endpoints exist for the data provided.

The relevant files are listed by the issue:
*`frontend/src/pages/ReviewPage.tsx`
*`frontend/src/services/shareService.ts`
*`api/routes/reviews.py`

However, `frontend/src/services/shareService.ts` does not exist, so I would need to look into `frontend/src/services/api.ts`.

The "done" should allow the user to physically generate a link and open it to see a summary of their review from the reviews API route. On the summary page, the page should include how much time left does the page have until expiration (or when the page expires). Additionally, the link should be accessible by any user.

*Part 2*: I chose a Tier 2 issue since I've worked on open-source style projects in the past, especially as a technical lead for a project at my university. I've worked on a few development teams also! I'm also fairly familiar with front-end development (especially in React) and would like to expand my knowledge through working thorugh this issue.

*Part 3* The relevant code is found in the relevant files above. The button is found in `frontend/src/pages/ReviewPage.tsx` I will be using the `get_review_endpoint` endpoint found in `api/routes/reviews.py`.

I would need to write a new test case to check for the 30-day deletion system, and unique link generation, which would be found in `tests/unit/test_review_service.py` or `frontend/src/test/setup.ts`.

*Part 4* The issue provides an estimate of 5-8 hours for completing this issue, which should be ample time for Weeks 8-9. The only major thing I'm doing is working on a game jam and contributing towards other projects. Only 1 student within my section is already working on the issue. There are no open blockers or dependencies for issue #101 also.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/anthonyle1/pathreview/commit/eb3dd4fc8da32c4244912066f22102dcf492f4ec

**Reproduction summary:**
I reproduced the issue by following the user workflow to "share" the link they provided. The link is able to be shared, but when opening the link to an incognito tab that is signed out, the user is prompted to log-in instead of viewing the shared review page.


**PLAN.md link:** https://github.com/anthonyle1/pathreview/blob/feat/101-review-copy-link/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
How to handle link regeneration + privacy? 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the entire changes defined in PLAN.md, making new API endpoints and editing the database schema, creating a new share page accessible by any user, and implemented tests to ensure link expiration.

**Next steps:**
I'm working on doing a PR review through Slack and getting ready for submission!

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/537

**Branch:** Add a "Copy link" button to share a public review summary

**What you built:**
I adjusted the Reviews database schema to include a public/private column and a date expiration column. Additionally, I created a new SharePage page as a place to display ReviewPage information. I handled link expiry after 30 days also. 

**Tests added or updated:**
In `tests\unit\test_review_service.py`, I added test cases to check functionality for `share_review` and `get_shared_review` functions. It covers link generation on first share, expiry-trigger regeneration, and public-access checks.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [Shawn Blackman](https://github.com/sh4wnbk) 

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
The reviewer commented on both pros and cons of my solution. He mentioned that it was a good idea to use uuid4 to prevent links to be guessable. Additionally, he mentioned that he appreciated including the is_public column to have expire links die at the endpoint. He mentioned that it may have been a good idea to have a seperate table for shared links rather than to include them in the review table, as an extra layer of protection since both private and public endpoints pull from the same database table. 

**How you responded:**
Since I was running low on time when submitting, I didn't have much time to address the database change. He also mentioned how I left parts of my notebook blank, so I corrected that.

---

### Reflection

**What was harder than you expected?**

I didn't anticipate the level of scope the issue handeled. I didn't really expect to change a lot of the existing API endpoints due to changes made in the database schema and building logic for new data endpoints. 


**What did you learn about working in a large codebase?**

I think it was difficult overall to be working with a lot more restrictions in place. For this project, it was the first time I was working with a test suite in a full-stack project, so some things such as checking test cases before starting to code was something I was not used to. Additionally, the review stages can add some extra time to ensure consistency with the entire project. When working on personal projects, often you're the only person or in a small group working on the code. This leads to more leniency on code style.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

AI was really helpful with being able to identify where the issue was and what relevant parts of the code are isolated with this feature. Since I forgot to check my test cases initially, I asked Claude to compare the test suite from before and after the committed code made on my PR request. I didn't really need much help beyond what AI gave me, but having the extra oversight from the PR review was helpful.

**What would you do differently if you started over?**

With this issue specifically, I should've had a seperate table that was linked to the Reviews table through a foreign key. I think this would have saved on storage space long term and also helps prevent pages that do not have an existing public link to not be showcased. It also would have allowed for proper deletion of the link.

With the overall process, I need to be more aware of testing and implement it more into my code to better understand how I'm isolating my code to the specific issue.

**What are you most proud of from this module?**

I got to work on something beyond a frontend issue! Even though the issue itself was labeled as a frontend issue, I ended up working on features beyond frontend, especially on building new API endpoints to handle sharing logic.