## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary (101)

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

I have experience with React and TypeScript, and I am familiar with the basics of web development, as well as have worked in shared codebases before, so I believe I am experienced enough for a tier 2 issue.

I also recognize I will have to create a new route (API endpoint) in `reviews.py` to handle the link generation, connect it to a service that actually creates the link, and then add a physical button to the UI on the `ReviewPage` that calls that service.

**Problem summary:**
The issue is requesting a button be added to the UI that allows the user to create a link they can share with others of their review summary. The link should be to a read-only version of their review summary that does not require authentication and expires after 30 days. The button should say "Copy Link" and be placed on the review summary page of the app.

**Branch name:** feat/101-add-copy-link-button

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/IDLinares/pathreview/commit/c6fcdba8ec3f64edd09c970569163cd309517543

**Reproduction summary:**
First, I manually tested the "Share" button that is currently available on the review page and saw it simply copied the URL of the current page, so it is not performing the intended functionality of creating a public link to the review page that expires after 30 days.

As such, I created two new test files to test the functionality and implementation of this feature for when it is completed: a file for the eventual share service in the backend that creates the share link, and a file for the frontend that calls the share service and copies the link to the clipboard.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** No link

**Blockers or open questions:**
No blockers or open questions.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented all of the backend functionality for the "Copy Link" button feature as documented in the [PLAN.md](PLAN.md) file. I updated the `Review` model to include new columns for the shareable link token and expiration date and well as performed the migration to add the new columns to the database. Also, two new async functions were created in `core/services/share_service.py` to handle the creation and retrieval of the shareable link. Lastly, two new routes were created: one in `api/routes/reviews.py` to handle the creation of the shareable link and another in `api/routes/public.py` to handle the retrieval of the public review summary along with schemas for the responses from the two new endpoints. Unit tests were also created and ran for this new service and all tests have passed.

**Next steps:**
The rest of the week will be spent working on the frontend functionality, testing, and preparing the PR.

**Blockers:**
Since this is a full-stack feature, some changes have caused linter errors and warnings in areas downstream in files unrelated to the feature I am working on. I have had to work around them by updating type declarations for functions in the same file that might be unrelated to my feature and silence the linter for files that were downstream of changes in my current file. These errors already existed in the codebase but are now being caught by the linter due to an import in a staged file, such as `main.py`.

---

### Check-in 2 (end of week)

**PR link:** [PR link](https://github.com/ascherj/pathreview/pull/597)

**Branch:** feat/101-add-copy-link-button

**What you built:**

The existing "Share" button on the review page copied `window.location.href` to the clipboard — an authenticated URL that only the owner could access. This feature replaces it with a "Copy Link" button that calls a new backend endpoint to generate a time-limited, publicly accessible share token. Clicking the button writes a public URL (`/public/reviews/<token>`) to the clipboard that anyone can open to access a read-only summary of the review without logging in. Tokens are valid for 30 days with expired tokens returing a 410 Gone response with a clear message to the recipient. A new PublicReviewPage renders the review in a self-contained read-only layout with no navigation or action buttons.

**Tests added or updated:**

- `tests/unit/test_share_service.py` — 11 unit tests covering both service functions (generating and retrieving the share link) across all token states (no token, valid token, expired token, non-owner)
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` — updated mock paths from '../' to '../../' to correctly intercept imports; 7 tests covering the Copy Link button addition to the review page (happy path + edge cases)

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:**

none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No — still awaiting review

**Summary of feedback:**

The reviewer comments that I correctly identified the security gap with the old "Share" button as it copied an authenticated URL to the clipboard with no real sharing capabilities. The judgemnt call on using error codes 410 vs 404 for expired vs unknown tokens is also correct HTTP sematics. They also agreed on the fields I excluded from the schema for the public review summary as well as the flags I made for the adjacent fixes I made in my PR to allow it to go through (such as the "silent" mypy workaround for the linting errors). Overall, the reviewer states the full-stack feature is solidly implemented and well-tested.

**How you responded:**

I thanked the reviewer for their feedback (PRs are not actually going to be merged for this project, but the feedback seems like the PR would likely have been merged).

---

### Reflection

**What was harder than you expected?**

The hardest part was making sure all of the tests were passing and that the linter was not complaining about any of the changes I made, especially since I made changes across both the front and backend. With many files being touched, it was crucial to make sure all conventions were being followed and that I was not introducing any new linting errors.

**What did you learn about working in a large codebase?**

When working in a well established codebase, it takes some time to get used to the patterns and convention of the codebase, especially if I already have my own habits and preferences for tools or setup. The more familiar you are with the codebase, the more you can take advantage of the tools and features that are already in place.

**How did AI tools help — and where did they fall short?**

AI tools were most helpful in explaining different parts of the codebase and how they were relevant to the feature I was working on, as well as for adjusting any functions or code that I wrote to match the conventions of the codebase.

I did need to make adjustments to the AI tool's suggestions to make sure it followed my idea of what a "read-only" review summary should look like. I adjusted the AI tool's output to make sure all the texts for the "read-only" summary was already open and visible, instead of in interactive dropdowns like on the authenticated review page.

**What would you do differently if you started over?**

If I started over, I would plan out my test files and cases more thoroughly before writing any code. I do prefer following a test-driven development approach, so I had written tests first in this case, but I ended up changing my implmentation of the updated schema for the Review model. I then had to go back and update the tests to match the new schema or they would have continuted to fail.

**What are you most proud of from this module?**

I successfully navigated an unfamiliar codebase and implemented a full-stack feature that was well-tested and well-documented. I also received positive feedback from the reviewer and did not encounter any major issues with the codebase or the feature.
