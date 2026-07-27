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
