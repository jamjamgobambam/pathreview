## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [ X ] Tier 2  [ ] Tier 3

Tier 2 fits my current scope because the feature spans both the frontend and backend — it requires building a new UI button in React, a service layer for generating share tokens, and a new API route in Python. I have prior experience with full-stack development, so I'm comfortable working across those layers, but the token expiry logic and public-access design add enough complexity to make this a meaningful challenge rather than a trivial addition.

**Problem summary:**
Users currently have no way to share their review summary with others — there is no shareable link feature in the application. The missing functionality should allow a user to generate a public, read-only link to their review summary that anyone can view without needing to log in. A successful fix would add a "Copy link" button to the review page that creates a time-limited share token (expiring after 30 days) and returns a public URL. This primarily affects `frontend/src/pages/ReviewPage.tsx`, `frontend/src/services/shareService.ts`, and `api/routes/reviews.py`.

**Branch name:** feat/101-copy-link-button

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/830462d29af84a0ad3bed316b4756ecb026078bb

**Reproduction summary:**
I confirmed the gap by running the app locally and clicking the existing Share button on a completed review. The button copies the current page URL to the clipboard, but that URL requires authentication — opening it in an incognito window redirects to the login page instead of showing the review. I also audited the codebase and found that `frontend/src/services/shareService.ts` does not exist, `api/routes/reviews.py` has no endpoint for generating or validating share tokens, and there is no database model for storing tokens. The public shareable link feature is entirely unimplemented.

**PLAN.md link:** https://github.com/rose413/pathreview/blob/feat/101-copy-link-button/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I am uncertain whether other files beyond the three listed in the issue will need to change. Specifically, I expect to also need a new database model for share tokens, an Alembic migration, and a new Pydantic schema — none of which are mentioned in the original issue description.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-task 1 — ShareToken model + migration
Sub-task 2 — Pydantic schemas
Sub-task 3 — Backend endpoints

**Next steps:**
Sub-task 4 — Frontend service
Sub-task 5 — Update ReviewPage
Sub-task 6 — Public share page + frontend route

**Blockers:**
There are no blockers so far.

### Check-in 2 (end of week)

**PR link:** [\[link to your submitted pull request\]](https://github.com/ascherj/pathreview/pull/896)

**Branch:** feat/101-copy-link-button

**What you built:**
Added end-to-end support for shareable public review links. On the backend, a new `ShareToken` database model stores cryptographically random, 30-day expiring tokens linked to reviews; two new API endpoints handle token generation (`POST /reviews/{id}/share`, auth-protected and idempotent) and public retrieval (`GET /reviews/public/{token}`, no auth, returns 410 for expired tokens). On the frontend, a new `shareService.ts` calls the generate endpoint, the Share button on `ReviewPage` was updated to copy the returned URL to the clipboard with inline loading/success/error feedback, and a new unauthenticated `/share/:token` page renders the review score and feedback sections for any recipient.

**Tests added or updated:**
- `tests/unit/test_share_routes.py` — 7 tests covering the happy path for token generation, idempotency (returning an existing active token), 404 when the review is not found, 400 when the review is not complete, successful public retrieval, 410 Gone for expired tokens, and 404 for unknown tokens.
- `tests/unit/test_share_token_model.py` — 20 tests covering column defaults (auto-generated UUID id, `secrets.token_urlsafe` token), uniqueness, nullability constraints, the `share_tokens` table name, `__repr__` format, and expiry comparison logic.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
I got no reviews at all.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
N/A
---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
It was hard to understand the codebase at first since there were a lot of different components.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
It is very important to learn how to read other people's code and to understand how their system is structured.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
It was useful to use Claude to summarize the codebase and to point out important information about the Dockerfile and the backend.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would do more time planning and really understanding the codebase before starting the implementation.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I'm proud of being able to read this codebase, understand it, and be able to implement the plan using Claude effectively.