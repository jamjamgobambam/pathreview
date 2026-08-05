# Problem Summary

Issue: Add a Copy link workflow to share a public review summary (Issue #101).

Current behavior:
- The Review page Share button copies the current browser URL, which points to a protected route.
- Backend review endpoints require authentication and ownership checks.
- No public review token or unauthenticated share endpoint exists.

Expected behavior:
- Users can generate a shareable public URL for a review.
- Anyone with that URL can view a sanitized review summary without logging in.
- Private review endpoints remain protected.

---

# Root Cause

The sharing flow is incomplete across database, service, API, and frontend layers:

1. Data model gap
- Review model has no share token field to represent a public share identifier.

2. Service layer gap
- Review service has ownership-scoped retrieval only.
- No method exists to generate, persist, rotate, or query by share token.

3. API gap
- All current /reviews routes depend on auth middleware.
- No public endpoint exists for share-token lookup.

4. Frontend routing/UI gap
- Review page is behind protected routing.
- Share button only copies a private route URL and does not create a public URL.

---

# Proposed Solution

Implement a token-based public sharing flow:

1. Add share_token to Review model
- Nullable, unique, indexed string token.
- Generated only when user requests sharing.

2. Add backend share methods
- Generate token endpoint for owners of the review.
- Public read endpoint that fetches a review by token and returns sanitized fields.

3. Update frontend sharing behavior
- Replace current Share handler with flow that requests (or reuses) token.
- Copy public URL (for example: /shared/{token}) to clipboard.

4. Add a public frontend page
- New route/page for public read-only summary.
- No auth required.

5. Define explicit inputs and outputs for the new flow
- Service input/output contracts in core/services/review_service.py:
  - create_or_get_share_token(review_id: UUID, user_id: UUID) -> str
  - get_review_by_share_token(share_token: str) -> Review | None
- API contract in api/routes/reviews.py and api/schemas/review.py:
  - POST /reviews/{review_id}/share (auth)
    - Input: path review_id, bearer token user context
    - Output: {"share_token": string, "share_url": string}
  - GET /reviews/share/{share_token} (public)
    - Input: path share_token
    - Output: sanitized review payload only
      {"id", "status", "sections", "overall_score", "created_at"}
- Frontend contract in frontend/src/services/api.ts and frontend/src/pages/ReviewPage.tsx:
  - Input: reviewId from route params on review page
  - Output: copied public URL and success/failure UI state

---

# Implementation Steps

1. Locate affected files and confirm existing patterns for auth-protected and public routes.
2. Add share_token field and migration.
3. Add service methods:
   - create_or_get_share_token(review_id, user_id)
   - get_review_by_share_token(share_token)
4. Add API routes:
   - POST /reviews/{review_id}/share (auth required)
   - GET /reviews/share/{share_token} (public)
5. Add schema updates for share response and public review response.
6. Update frontend API client to call share endpoints.
7. Update Review page button label and behavior to Copy link.
8. Add public route and public review page component.
9. Add unit/integration tests for service and API behavior.
10. Run tests and manual regression checks.

---

# Files to Modify

- core/models/review.py
  - Add share_token column and index.

- alembic/versions/<new_migration>.py
  - Add migration for share_token schema change.

- core/services/review_service.py
  - Add token generation/query functions.

- api/schemas/review.py
  - Add share/public response models.

- api/routes/reviews.py
  - Add share token creation route and public token lookup route.

- frontend/src/services/api.ts
  - Add methods for generate share link and get public review.

- frontend/src/App.tsx
  - Add public route for shared review page.

- frontend/src/pages/ReviewPage.tsx
  - Replace Share behavior to copy public share URL.

- frontend/src/pages/<new_shared_review_page>.tsx
  - Render public read-only review summary.

- tests/unit/test_review_service.py
  - Add tests for token generation and token lookup.

- tests/integration/<new_reviews_share_test>.py
  - Add API tests for auth/public route behavior.

---

# Risks

- Breaking changes
  - Migration errors or uniqueness constraints in core/models/review.py and alembic/versions/<new_migration>.py could break review writes if misconfigured.
  - Investigation path: run alembic upgrade on a seeded DB, then create/list reviews via existing /reviews endpoints.

- Security concerns
  - Public endpoint in api/routes/reviews.py could expose too much data if ReviewResponse is reused instead of a constrained public schema in api/schemas/review.py.
  - Token entropy in core/services/review_service.py may be insufficient if token generation uses predictable/randomly weak values.
  - Investigation path: verify schema excludes profile_id and user identifiers; verify token generator uses a cryptographically secure source.

- Backward compatibility
  - Existing reviews will have null share_token until generated, which can break frontend assumptions if ReviewPage.tsx expects a token to always exist.
  - Investigation path: test old reviews with no token and ensure POST /reviews/{review_id}/share creates one on demand.

- Edge cases
  - Deleted review with stale token should return 404 from GET /reviews/share/{share_token}.
  - Token regeneration policy (reuse vs rotate) affects old link validity in core/services/review_service.py.
  - Clipboard API denial in frontend/src/pages/ReviewPage.tsx must show fallback/error state instead of silent failure.

---

# Unknowns

- Revocation behavior in core/services/review_service.py:
  - Should we support explicit revoke endpoint now, or defer to token rotation?
- Expiration policy in core/models/review.py:
  - Do we need expires_at for share tokens, or non-expiring links for MVP?
- Public payload scope in api/schemas/review.py:
  - Are confidence and suggestions safe for public exposure, or should we hide confidence?
- Token lifecycle in core/services/review_service.py:
  - Should POST /reviews/{review_id}/share be idempotent (return existing token) or rotate each request?
- Abuse protections in api/routes/reviews.py and safety/rate_limiter.py:
  - Should GET /reviews/share/{share_token} be integrated with current rate limiting before release?

---

# Testing Plan

Existing tests to run:
- tests/unit/test_review_service.py
- tests/integration review-route tests (existing and new)

New tests to add:
- Unit: token creation, uniqueness handling, token lookup success/failure.
- API integration:
  - POST share route requires auth and ownership.
  - GET public share route works without auth.
  - Invalid/unknown token returns 404.

Manual testing:
1. Log in, open completed review, click Copy link.
2. Open copied link in private/incognito window.
3. Verify review summary loads without login.
4. Verify protected /reviews/{review_id} still redirects/rejects unauthenticated users.

Regression testing:
- Re-run unit and integration suites.
- Validate no regressions in review creation/status polling/export.

---

# Estimated Difficulty

Medium.

Reason:
- Cross-layer change (DB + backend + frontend + tests) but scoped to one feature.
- Requires careful auth/public boundary design and token security.
- Existing architecture already provides clear service and routing patterns to extend.