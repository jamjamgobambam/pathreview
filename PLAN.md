# Solution plan

**Issue:** POST /reviews endpoint has no test for when the profile has no ingested documents
https://github.com/ascherj/pathreview/issues/88

### Understand

Expected (per the issue title): route-level test coverage for `POST /reviews`
should include the case where a profile has no ingested documents.

Actual: `tests/unit/test_review_routes.py` doesn't exist — there is no
route-level test coverage at all for `POST /reviews`, for any case.

While reproducing, I traced the actual runtime behavior for this case (see
JOURNAL.md "Reproduction" entry) and confirmed there's no validation gap
hiding behind the missing test, either — `create_review` never checks for
ingested sources, and `process_review`'s agent/RAG steps return hardcoded
placeholder content regardless of `ingestion_results`, so a profile with zero
sources still produces a `status="complete"` review with fabricated feedback.

Scoped fix for this ticket: add tests that document this real current
behavior. Changing the route/service layer to actually reject or flag
no-document profiles is a separate, larger change and is explicitly out of
scope here (would need a product decision on the right response — e.g. a 4xx
at creation time vs. a "failed"/"insufficient_data" status after processing).

### Map

Files touched:
- `tests/unit/test_review_routes.py` (new) — route-level tests for
  `POST /reviews`, `GET /reviews/{id}`, `GET /reviews`, `GET /reviews/{id}/status`,
  focused on the no-ingested-documents case for the create endpoint.

Files read/depended on but not modified:
- `api/routes/reviews.py` — endpoint under test.
- `core/services/review_service.py` — `create_review`, `process_review`.
- `api/schemas/review.py` — `ReviewCreate`/`ReviewResponse` shapes.
- `api/middleware/auth.py` — `get_current_user` dependency to override.
- `core/database.py` — `get_db` dependency to override.
- `tests/unit/test_review_service.py` — existing patterns/fixtures to follow
  (with one correction, see Risks).

### Plan

1. Set up a `TestClient(app)` fixture with `app.dependency_overrides` for
   `get_current_user` (return a fake `User`) and `get_db` (return a mock
   session) — this repo has no existing route-test fixture, so this is new.
2. Write the core regression test: `POST /reviews` for a profile with
   `github_username=None`, `portfolio_url=None`, `resume_text=None` returns
   `200` with `status="pending"` (documents current behavior — no validation
   error, by design of this ticket's scope).
3. Add a test that runs the background `process_review` task through to
   completion for that same no-source profile and asserts it ends
   `status="complete"` with non-empty fabricated `sections` — this is the
   concrete "gap" the issue is really about, made visible as an assertion
   instead of a prose note.
4. Round out baseline coverage the file is missing entirely: happy-path
   `POST /reviews` with a normal profile, `GET /reviews/{id}` found/not-found/
   wrong-owner, `GET /reviews` pagination, `GET /reviews/{id}/status`.
5. Run `make test-unit` (or `pytest tests/unit/test_review_routes.py -v`),
   confirm everything passes, and update JOURNAL.md if the understanding
   shifts while writing tests.

### Inputs & outputs

Input: the existing, unmodified `api/routes/reviews.py` and
`core/services/review_service.py` behavior.
Output: a new test file that passes against current behavior and fails loudly
if a future change silently alters what happens for a no-document profile
(e.g. if someone "fixes" validation without updating/removing this test, or
regresses it back to fabricated feedback after a real fix lands).

No production code changes in this ticket's scope.

### Risks & unknowns

- **Mocking `AsyncSession.execute()`**: `test_review_service.py` currently has
  13/19 tests failing because `AsyncMock()` auto-specs child attributes
  (`.scalars()`) as `AsyncMock` too, producing an unawaited coroutine instead
  of the configured return value. Must use `Mock()` for the `Result` object
  returned by `execute()`, only `db.execute` itself as `AsyncMock`. Confirmed
  this works in the reproduction script.
- **Auth override plumbing**: haven't yet confirmed the exact `User` fields
  `get_current_user` callers depend on beyond `.id` — need to check
  `core/models/user.py` before building the fake user.
- **Background task execution in tests**: `TestClient` runs `BackgroundTasks`
  synchronously by default, but need to confirm this holds with the
  async route + async background function combination here, or call
  `process_review` directly (bypassing the route) for step 3 if not.
- **Scope creep temptation**: it would be easy to slide into "fixing" the
  validation gap while writing these tests. Explicitly not doing that here —
  flagging it as a follow-up issue instead, per the journal's stated scope.

### Edge cases

- Profile has some but not all sources (e.g. only `github_username` set) —
  out of scope for this ticket's specific case, but worth one test to show
  the boundary of "no ingested documents" vs. "partial documents".
- `profile_id` in `ReviewCreate` that doesn't exist / doesn't belong to the
  current user — currently unchecked in `create_review`; document actual
  behavior rather than assume.
- Concurrent/duplicate `POST /reviews` for the same profile — not covered;
  noting as out of scope, not silently ignoring.
