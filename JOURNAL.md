# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary #101

**Tier:** [ ] Tier 1 [✔] Tier 2 [ ] Tier 3

**Problem summary:**
Right now, the only way to see someone's review summary on PathReview is to be logged into that person's own account, so there's no easy way to hand results to a mentor, recruiter, or peer for feedback. This issue calls for a "Copy link" button on the review page that generates a unique, public URL leading to a read-only version of the summary — no login required. It also needs the link to stop working automatically after 30 days, so a summary isn't left permanently exposed. Getting this working means adding sharing logic to the frontend service and a matching endpoint on the backend to create and validate these time-limited links.

**Why I chose this issue:**
I picked a Tier 2 issue since I'm very comfortable with React from building frontend applications regularly, but have less hands-on experience with the backend/API side of a codebase like this one. I specifically searched the issue tracker for frontend-facing issues, and this one stood out because most of the work (the button, the copy-to-clipboard interaction, and calling the share service) is familiar React territory to me, while the small backend piece (the share-token endpoint) gives me a manageable way to touch the API layer without owning unfamiliar backend logic end-to-end. Also, the 5–8 hour estimate and the scoped files in the issue description felt achievable for this week.

**Branch name:** `feat/101-copy-link-share-summary`

**Setup confirmation:** [✔] App runs locally at localhost:5173

**Cohort ledger:** [✔] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ChinoUkaegbu/pathreview/commit/00997be5dba1b2456fd3334325b1834f0cd68592

**Reproduction summary:**
I found that the "Share" button in `ReviewPage.tsx` already exists and copies a link, but it copies the private, authenticated review URL — which fails for anyone but the logged-in owner since `GET /reviews/{review_id}` requires auth and filters by owner ID, with no public/token-based route or expiration logic anywhere in the codebase.

**PLAN.md link:** https://github.com/ChinoUkaegbu/pathreview/blob/feat/101-copy-link-share-summary/PLAN.md

**Walkthrough video (recommended):** https://drive.google.com/file/d/1-ddXpmBNxSHcOqXTOvw0nA8hOatsjg7c/view?usp=sharing

**Blockers or open questions:**
Still unsure whether share tokens should be actively invalidated when a new one is generated (or if multiple valid tokens per review is fine), and want to confirm the best pattern for mixing an authenticated and a public route within the same FastAPI router.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Backend is fully implemented and committed: added the `ShareLink` model and migration, the `create_share_link` and `get_review_by_share_token` service functions, and the two new API endpoints (`POST /reviews/{review_id}/share` and `GET /reviews/shared/{token}`). Verified end-to-end via Swagger — token generation, public no-auth fetch, and 404s on invalid/unowned requests all work as expected. Also caught and fixed a timezone bug (naive vs. aware datetime comparison) in the `ShareLink.is_expired()` check.

**Next steps:**
Wire up the frontend: add `createShareLink`/`getSharedReview` to `api.ts`, fix `handleShare()` in `ReviewPage.tsx` to use a real share token instead of the raw page URL, and build the new public `/shared/:token` route and page. Then write unit tests for the new service functions.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/321

**Branch:** `feat/101-copy-link-share-summary`

**What you built:**
A working public share-link feature: clicking "Share" on a review now generates a real, token-based shareable link that opens a read-only view with no login required, and automatically expires after 30 days.

**Tests added or updated:**
Added 6 tests to `tests/unit/test_review_service.py` covering `create_share_link` (owned review success, not-found/not-owned case) and `get_review_by_share_token` (valid token, unknown token, expired token, and orphaned token whose review no longer exists).

**Self-review confirmation:** [✔] make check passes  [✔] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [✔] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Honestly, the hardest part was setting up the environment before I could even begin to make any changes. I remember trying to use the Ubuntu terminal, updating it twice (from 20.04 to 24.04), and then realizing it would be easier to work with Git Bash since the instructions had outlined details specific to it. Setting up Docker was also challenging since I hadn't used it recently but eventually, I was able to set up the environment. I had in no way anticipated that that would have been such a challenge but I'm happy I was able to surmount it.

**What did you learn about working in a large codebase?**
I learnt a lot but perhaps the most important thing was following conventions outlined in production code. I had some VSCode extensions (Prettier for instance), that would entirely reformat code that fit the way I personally like to write my code, but was not in sync with the conventions of the codebase. And so learning to first identify what the standards were and then abiding by them was really important. It's also inspired me to define the standards I use for my own personal code so if someday somebody else contributes to it, they can understand what to do!

**How did AI tools help — and where did they fall short?**
AI tools were very helpful in first planning how we would implement the feature before actually writing the code. I think it's very important to have that plan beforehand, especially for an issue that touches on multiple parts of the system, so that you're grounded in the small, incremental steps you'll be implementing. In terms of where they fell short, I find that providing too much information to the AI tools can be overkill at times and so I opted to not provide the entire codebase to the tool. As a result, I was able to make decisions such as keeping the backend returning just the token for the shared review and having the front end build the full URL using `window.location.origin`, rather than adding new config just for this one feature.

**What would you do differently if you started over?**
Outside of making sure the environment is up and running, I'd definitely run the tests and all the `make` commands beforehand so that I would have some sort of baseline to reference my changes against, to see if any additional errors surface. I actually forgot to do that for this project and panicked a bit before learning I could run `git checkout` on an earlier commit hash, run whatever tests and commands I had to confirm and then return to my actual branch. I'm glad I was able to learrn something new but definitely, if I started over or when I contribute to new projects, I'll be hyper aware of making sure I know the current state of the system before I add features or make fixes.

**What are you most proud of from this module?**
I'm very proud of how much I was able to put all that I had previously learnt into practice in this module. For instance, I used my previous knowledge with frontend development to handle the UI for the share button, choosing to disable it when clicked and display a spinner while the review link is being generated. I also got to use the git commands I've learnt from working on projects throughout this class while implementing the feature I had chosen. I'm a huge fan of seeing how the stuff I've learnt translates into action and it was really great to see that show up here as well!
