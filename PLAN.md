## Solution plan

**Issue:** [Review creation does not verify profile ownership (#163)](https://github.com/ascherj/pathreview/issues/163)

### Understand

`POST /reviews` authenticates the caller in `api/routes/reviews.py` and passes both
`data.profile_id` and `current_user.id` to `create_review()`. The root cause is in
`core/services/review_service.py`: `create_review()` ignores `user_id` and inserts a
pending `Review` using the caller-supplied profile ID without first querying `Profile`.
An authenticated user who knows another user's profile UUID can therefore create a
review and start background processing for that profile.

Expected behavior is that review creation succeeds only when the profile exists and
`Profile.user_id` matches the authenticated user. A missing or unowned profile should
produce the same 404 response so the endpoint does not reveal another user's profile.
Actual behavior is a successful pending review for either profile.

### Map

- `core/services/review_service.py` — add the ownership-scoped profile lookup to
  `create_review()` and return no review when it does not match.
- `api/routes/reviews.py` — translate a missing/unowned result into a 404 before
  scheduling `process_review()`.
- `tests/unit/test_review_service.py` — keep the reproduction regression and add
  coverage for both rejected and owned-profile creation paths.
- `tests/security/` — investigate whether the existing test setup can support a
  two-user endpoint-level regression; add one here if it can do so without duplicating
  the unit test's mocks.

No schema, model, migration, or frontend change is expected. `core/models/profile.py`
and `core/models/review.py` define the ownership relationship but should remain
unchanged.

### Plan

1. Query `Profile` in `create_review()` using both `Profile.id == profile_id` and
   `Profile.user_id == user_id`, following `core/services/profile_service.py` and the
   existing review read paths.
2. Return `None` before constructing, adding, committing, or refreshing a `Review`
   when the ownership-scoped query has no result; update the return annotation to
   `Review | None`.
3. Update `create_review_endpoint()` to return `404 Profile not found` for that result
   and ensure no background task is scheduled on the rejected path.
4. Update service tests so owned-profile creation still yields a pending review and
   the cross-user reproduction proves there is no database write. Add route/security
   coverage for the 404 and absent background task if the current fixtures support it.
5. Run the focused review-service/security tests, then the complete test suite and
   lint/type checks; distinguish any pre-existing failures from regressions caused by
   the fix.

### Inputs & outputs

The input is an authenticated user's UUID plus the profile UUID supplied in a
`POST /reviews` JSON body. For a profile owned by that user, the output remains a
persisted `Review` with `status="pending"`, followed by the existing background task.
For a nonexistent or differently owned profile, the service produces no review and
the route returns HTTP 404 with `{"detail": "Profile not found"}`; no review row is
inserted and no processing task is queued.

### Risks & unknowns

- Existing happy-path mocks in `tests/unit/test_review_service.py` do not configure
  `db.execute()`. Adding a lookup will require those fixtures/tests to return an owned
  profile, or unrelated creation tests may fail for mock-configuration reasons.
- `Profile.id` and `Profile.user_id` are typed as strings in
  `core/models/profile.py`, while the service accepts `UUID`. SQLAlchemy/PostgreSQL
  currently handle this elsewhere, but the query should follow the proven pattern in
  `get_profile()` rather than introduce manual conversion.
- The route currently assumes `create_review()` always returns a `Review` and accesses
  `review.id` immediately. The `None` check must occur before `add_task()` to prevent
  processing an unauthorized profile.
- The repository has no endpoint integration tests today. If adding one requires a
  large new database/auth harness, the scoped service regression plus a mocked route
  test may be the safer Week 9 boundary.
- The current pre-commit hooks report unrelated lint and mypy failures in the existing
  review service/test file. Validation must record these separately rather than
  hiding them or expanding this security fix into a broad cleanup.

### Edge cases

- The profile UUID exists and belongs to the authenticated user: creation succeeds
  exactly once and processing is scheduled.
- The profile UUID exists but belongs to a different user: return 404, write nothing,
  and schedule nothing.
- The profile UUID does not exist: use the identical 404 response and side effects as
  the cross-user case to avoid profile enumeration.
- The request contains a malformed UUID: preserve FastAPI/Pydantic's existing 422
  validation before the service is called.
- The ownership query raises a database error: preserve the route's rollback and 500
  behavior; do not convert infrastructure failures into 404 responses.
- Ownership changes or the profile is deleted between validation and insertion: assess
  whether the foreign key/transaction behavior is sufficient and ensure failures do
  not leave or schedule a usable unauthorized review.
