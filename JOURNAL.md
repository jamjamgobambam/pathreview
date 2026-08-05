# Week 7 — Issue Journal

## Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** Tier 2

---

## Problem Summary

Currently, portfolio review results are only accessible to authenticated users who own them through the private `/reviews/{review_id}` API endpoint. Users cannot share their portfolio reviews with others (mentors, employers, colleagues) without granting full account access. This feature requires implementing a public review sharing mechanism by: (1) adding a unique public share token to the Review database model, (2) creating a new public API endpoint that fetches review summaries by share token (without authentication), and (3) adding a "Copy link" button in the ReviewPage frontend component that generates and copies a shareable URL. The implementation spans the Review model (`core/models/review.py`), review service (`core/services/review_service.py`), API routes (`api/routes/reviews.py`), and the ReviewPage component (`frontend/src/pages/ReviewPage.tsx`).

---

## "Is This Right for Me?" Checklist

### Part 1 — Understanding the Issue

- [x] **Can I explain what this issue is asking for in my own words?**
  - Yes. Users need to share portfolio reviews publicly without granting account access. Solution requires: a share token mechanism, public API endpoint, and UI "Copy link" button.
  
- [x] **Do I understand which part of the app is affected?**
  - Yes. Located files:
    - `core/models/review.py` — Add public share token field
    - `core/services/review_service.py` — Service methods for token generation and retrieval
    - `api/routes/reviews.py` — New public endpoint for fetching by share token
    - `frontend/src/pages/ReviewPage.tsx` — UI button to generate and copy link
  
- [x] **Do I understand what "done" looks like?**
  - Before: Users see current Share button that only copies internal authenticated URL; reviews require login to access
  - After: Users see "Copy link" button that generates a public share URL with unique token; unauthenticated users can view shared review via public endpoint

### Part 2 — Tier Fit

- [x] **Is the tier a realistic match for where I am right now?**
  - Yes. This is Tier 2 (requires understanding module interactions). I have prior open-source contribution experience and this involves:
    - Database model modification (1 new field)
    - Service layer update (token generation/retrieval)
    - API endpoint addition (1 new public route)
    - Frontend button implementation (existing component update)
  - Scope is well-contained within review subsystem, not cross-cutting

### Part 3 — Codebase Readiness

- [x] **Can I find the relevant code?**
  - Yes. Reviewed:
    - Review model: Fields, relationships, migrations
    - Review service: CRUD operations, query patterns
    - Reviews API routes: Endpoint structure, auth patterns, response schemas
    - ReviewPage component: Current Share button implementation
  
- [x] **Do I understand the surrounding code well enough to change it safely?**
  - Yes. I understand:
    - Database models use SQLAlchemy with UUID primary keys
    - Services follow async pattern with dependency injection
    - API routes use FastAPI with auth middleware
    - Frontend uses React hooks and TypeScript
  - Can predict changes: adding String field to model, adding service methods, adding new route, updating button handler
  
- [x] **Have I read the relevant test file?**
  - Need to verify test file structure (will check in `tests/unit/`)

### Part 4 — Scope and Time

- [x] **How many others are already working on this issue?**
  - Checked cohort ledger: Issue #101 has minimal claims, reasonable crowd level
  
- [x] **Is the scope realistic for Weeks 8–9?**
  - Yes. Tier 2 scope (8-12 hours estimated):
    - Model/migration: 1-2 hours
    - Service/API: 2-3 hours
    - Frontend: 1-2 hours
    - Tests: 2-3 hours
    - Testing/debugging: 1-2 hours
  - Total: ~9-12 hours over 2 weeks is achievable with focused work
  
- [x] **Are there any blockers or dependencies?**
  - No blockers. Issue is self-contained within review subsystem. No dependencies on other issues.

---

## Implementation Plan

### Phase 1: Backend Foundation (Model & Migration)
1. Add `share_token` field to Review model (nullable, unique, indexed)
2. Create database migration
3. Add token generation utility function

### Phase 2: Service & API Layer
1. Add service methods for:
   - `generate_share_token()` — create new token when sharing
   - `get_review_by_share_token()` — retrieve review without auth
2. Add new public API route: `GET /reviews/share/{share_token}`
   - No auth required
   - Returns sanitized review data (no sensitive fields)

### Phase 3: Frontend
1. Update ReviewPage component:
   - Add "Copy link" button (or enhance existing Share button)
   - Generate share token via API if not already set
   - Copy public URL to clipboard
   - Show success confirmation

### Phase 4: Testing & Polish
1. Unit tests for service methods
2. API endpoint tests (public access, error cases)
3. Frontend component tests
4. Manual testing of full flow

---

## Verdict

✅ **Ready to claim.** All checklist items verified. Tier 2 scope is appropriate, codebase is well-understood, and timeline is realistic.

---

## Week 8

### Issue Worked On

- Issue link: https://github.com/ascherj/pathreview/issues/101
- Issue title: Add a Copy link button to share a public review summary
- Scope: Reproduce current behavior, trace root cause, and prepare implementation plan

### Week 8 Deliverable Links

- Reproduction commit: https://github.com/wiinc355/pathreview/commit/9f57a18
- PLAN.md: https://github.com/wiinc355/pathreview/blob/feat/101-public-review-sharing/PLAN.md
- Working branch URL: https://github.com/wiinc355/pathreview/tree/feat/101-public-review-sharing
- Walkthrough video (optional): Not recorded yet

### What I Learned

- The current Share button copies the current protected review URL, not a public URL.
- Review endpoints are ownership-protected through auth dependencies.
- There is no share token in the Review model, so there is no durable public identifier.
- A complete solution requires coordinated changes across model, service, API, frontend route, and tests.

### Reproduction Steps

Static/code-level reproduction (confirmed):

1. Open frontend/src/pages/ReviewPage.tsx and inspect handleShare.
2. Confirm it copies window.location.href directly.
3. Open frontend/src/App.tsx and confirm /reviews/:reviewId is wrapped by ProtectedRoute.
4. Open api/routes/reviews.py and confirm all review endpoints require get_current_user.
5. Search for share_token and /reviews/share references across backend/frontend files.
6. Observe there are no model/service/route/client implementations for public review sharing.

Command evidence used:

```bash
rg -n "share_token|/reviews/share|handleShare|path=\"/reviews/:reviewId\"|get_current_user" \
  core/models/review.py api/routes/reviews.py frontend/src/pages/ReviewPage.tsx frontend/src/App.tsx

rg -n "share_token|/reviews/share" \
  core/models/review.py api/routes/reviews.py core/services/review_service.py frontend/src/services/api.ts
```

Expected result:
- A Share/Copy link action should produce a public URL that works without authentication.

Actual result:
- Share currently copies only the authenticated page URL.
- No public token or public endpoint exists.

Additional local test baseline:

```bash
.venv/bin/pytest tests/unit/test_review_service.py -q
```

Observed output summary:
- Multiple existing failures unrelated to issue #101 (AsyncMock coroutine chaining in test setup).

### Challenges

- The issue requires cross-layer planning rather than a single-file fix.
- Existing test failures in test_review_service.py can mask confidence if not isolated.
- Public sharing design requires careful decisions on sanitization and token lifecycle.

### Research Performed

- Reviewed:
  - core/models/review.py
  - core/services/review_service.py
  - api/routes/reviews.py
  - api/schemas/review.py
  - frontend/src/pages/ReviewPage.tsx
  - frontend/src/services/api.ts
  - frontend/src/App.tsx
  - docs/SETUP.md and Makefile for local run/test workflows

- Traced call path:
  - ReviewPage Share click -> handleShare -> clipboard current URL
  - Route /reviews/:reviewId requires auth
  - Backend /reviews endpoints require get_current_user
  - No token-backed public retrieval path exists

### Solution Plan

- Added detailed plan in PLAN.md covering:
  - Problem summary
  - Root cause
  - Proposed solution
  - Implementation steps
  - Risks, unknowns, and testing plan

### Remaining Questions

- Should share tokens be revocable?
- Should tokens expire?
- Which fields are allowed in public response payloads?
- Should share creation be idempotent or rotate token each time?

### Next Steps

1. Implement model + migration for share_token.
2. Add service methods for token creation and public token lookup.
3. Add auth-protected share generation route and public share read route.
4. Update frontend API client and Review page Copy link behavior.
5. Add a public shared review page route/component.
6. Add tests for token flow and endpoint auth boundaries.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All backend sub-tasks from PLAN.md are done. Implemented `share_token` on the
Review model (`core/models/review.py`) with a matching Alembic migration
(`003_add_share_token_to_reviews.py`), added two service functions in
`core/services/review_service.py` — `create_or_get_share_token` (idempotent,
cryptographically secure `secrets.token_urlsafe`) and
`get_review_by_share_token` — plus the API layer: `POST /reviews/{review_id}/share`
(auth + ownership) and public `GET /reviews/share/{share_token}`, backed by new
`ShareTokenResponse` / `PublicReviewResponse` schemas that omit owner fields.
Frontend sub-tasks are also done: `api.ts` client methods, a public
`/shared/:shareToken` route, a new read-only `SharedReviewPage`, and the
ReviewPage "Copy link" flow with copied/error states.

**Next steps:**
Finalize unit tests, run the full self-review (`make check` / `make test-unit`),
get draft-PR feedback in Slack, and open the PR for review.

**Blockers:**
None. Noted a pre-existing environment quirk (the project virtualenv and
`docs/`/`.github/` had been copied into `core/`; restored the layout locally so
it does not pollute the PR) and heavy pre-existing failures in `make check` and
`make test-unit` unrelated to this issue (documented below).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/634

**Branch:** `feat/101-public-review-sharing`

**What you built:**
A token-based public review sharing flow. An owner clicks "Copy link" on their
completed review, which calls an authenticated endpoint that generates (or
reuses) a unique `share_token` and returns a `/shared/{token}` URL. Anyone with
that URL can view a sanitized, read-only summary via a public, unauthenticated
endpoint, while all existing private review endpoints stay auth-protected.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added a `TestReviewSharing` suite (7 tests)
covering token idempotency (reuse of an existing token), fresh-token generation
and persistence, `None` when the review is not owned/found, URL-safe token
charset, and share-token lookup success / unknown-token / empty-token cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> In this codebase both commands have **documented pre-existing failures**
> unrelated to issue #101. Baseline before my changes: `make test-unit` = 53
> failed / 375 passed; `make check` fails at `ruff` (182 errors), `black` (52
> files), and `mypy` (missing third-party stubs). After my changes:
> `make test-unit` = 53 failed / **382 passed** (my 7 new tests pass; the same
> 53 pre-existing failures remain — **no new failures**). My new Python files are
> black-clean and my two service functions are ruff/mypy-clean; the new route
> handlers intentionally follow the existing file's FastAPI patterns
> (`Depends()` defaults, `current_user.id`), so any lint/type notes they produce
> are the same categories already present on every pre-existing endpoint. Per
> the Week 9 guidance, "passes" here means my changes introduce no new failures.

**Draft PR feedback received from:** none (draft PR opened for peer review in Slack)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in on PR #634 by the end of the week.
Per the Summer 2026 course note, reviewer feedback on the upstream repo
(`ascherj/pathreview`) is not an active feature this term, so none was expected.
The PR remains open against upstream `main` with the full public-review-sharing
implementation and my 7 new unit tests.

**How you responded:**
No changes were required, since no feedback arrived. I did a final self-review
pass on the branch to confirm the PR is still in a mergeable, reviewable state:
the diff stays scoped to the review-sharing subsystem (model + migration,
service functions, two routes, schemas, frontend client/route/page), my new
Python files remain black-clean, and my 7 tests still pass on top of the same
53 documented pre-existing failures — no new failures introduced.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the feature logic — it was working *around* the state of
the codebase and local environment rather than *in* it. Two things surprised me.
First, the local environment was subtly broken in ways that had nothing to do
with my issue: the project virtualenv (and copies of `docs/` and `.github/`) had
been nested under `core/`, the Makefile expected a root `.venv` that didn't
exist, and the console-script shebangs pointed at a stale path — so I had to run
every tool in module form (`core/.venv/bin/python -m pytest|ruff|black`) instead
of the normal `make` targets. Second, `make check` and `make test-unit` had
heavy *pre-existing* failures (53 failing tests, 182 ruff errors, 52 unformatted
files, missing mypy stubs) before I touched anything. Separating "failures I
caused" from "failures that were already there" took real discipline and became
the whole basis of how I had to phrase my self-review. The actual token +
endpoint + button work was the *smaller* half of the effort.

**What did you learn about working in a large codebase?**
That "matching the house style" often matters more than writing what you'd
consider the cleanest code. In `api/routes/reviews.py`, the existing endpoints
uniformly use `Depends()` in default arguments (which ruff flags as B008), raise
bare `HTTPException` in except blocks (B904), and pass `current_user.id` as a
string where services annotate `UUID`. My instinct was to "fix" those in my new
handlers — but doing so would have made my code inconsistent with every other
endpoint and would have signaled to a reviewer that I didn't understand the
conventions. So I deliberately matched the existing patterns and documented that
choice. Contributing to someone else's production code is much more about
*fitting in* — respecting existing decisions, keeping the diff small and
scoped, and not surprising the maintainer — than about building my own project,
where I own every convention and can refactor freely. I also learned to design
for boundaries I couldn't see initially: sanitizing the public response so it
omits owner fields, keeping every existing private endpoint auth-protected, and
making token creation idempotent so re-clicking "Copy link" doesn't rotate a
link someone already shared.

**How did AI tools help — and where did they fall short?**
AI was most useful for *orientation and boilerplate*: quickly tracing the call
path (ReviewPage → handleShare → clipboard; the `/reviews/:reviewId` protected
route; the auth-gated backend endpoints), scaffolding the Alembic migration and
the new Pydantic schemas, and drafting test cases for the token flow. That
compressed hours of reading into minutes. Where it fell short was anything that
depended on the *specific broken state* of this repo — AI happily suggested
`make check` and `make test-unit` as if they'd pass cleanly, and couldn't have
known that the venv was misplaced or that 53 tests were already red for reasons
unrelated to my work. It also couldn't make the judgment call about whether to
match the existing B008/B904 "code smells" or fix them; that required
understanding the social context of a PR (don't surprise the maintainer), not
just the code. The security-sensitive decisions — using `secrets.token_urlsafe`
for the token, deciding which fields are safe to expose publicly — were things I
had to reason through and verify myself, not take on faith.

**What would you do differently if you started over?**
I'd validate the local environment *before* writing any code — run the test
suite on a clean checkout first to capture the true baseline, so I'd know from
day one exactly which failures were pre-existing instead of discovering it
mid-implementation. That baseline turned out to be the single most important
fact for my whole self-review, and I established it later than I should have.
I'd also open the draft PR earlier in the week to leave a real window for peer
feedback in Slack, rather than finishing most of the implementation first. On
planning, PLAN.md held up well, but I'd add an explicit "environment / tooling"
section to it next time, since that's where the actual friction lived.

**What are you most proud of from this module?**
The clarity and honesty of the self-review. It would have been easy to write
"make check passes" and move on, or to panic at 53 failing tests. Instead I
took the time to establish a real before/after baseline (53 failed / 375 passed
→ 53 failed / **382 passed**), prove my 7 new tests all pass, and document
precisely why the pre-existing failures aren't mine — including keeping my new
files black-clean and matching the existing lint patterns deliberately rather
than accidentally. Being able to defend exactly what my change does and doesn't
affect, in a messy real-world repo, is the skill I most wanted to build this
module.
