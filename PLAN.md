# pathreview (Issue #88) - PLAN.md

## Solution Plan

**Issue:** [POST /reviews endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

### Understand
When `POST /reviews` is called, `create_review_endpoint()` in `api/routes/reviews.py` (line 22) immediately calls `create_review()` to insert a review record and queues a background task. This is done without checking whether the profile has any ingested documents to analyze.

The background task, `process_review()` in `core/services/review_service.py` (line 82), calls `_run_ingestion_pipeline()` (line 197), which checks `profile.github_username`, `profile.portfolio_url`, and `profile.resume_text`. In the case that there are no ingested documents, all three fields are `None` and every branch is skipped. It returns `sources = []` with no error raised.

The downstream functions `_run_agent_orchestartion()` (line 282) and `_run_rag_retrieval_generation()` (line 307) ignore the empty list entirely and return hardcoded placeholder sections regardless of the input.

This means the review ends up being `"complete"` with fabricated feedback and no error was raised at any step.

**The expected behavior:** before creating the review record, check that the profile has at least one non-null, non-empty document field. If not, raise an HTTP 422 immediately. This prevents calling `create_review()` and queueing the background task.

**Root cause:** Missing pre-creation validation in `create_review_endpoint()` in `api/routes/reviews.py`.

### Map
The following are the files I expect to touch:
- `api/routes/reviews.py` — `create_review_endpoint()` (line 22): add a profile lookup and document check before the call to `create_review()` on line 36.
- `tests/unit/test_review_routes.py` — this file does not exist yet. I will create it and add a test that verifies the endpoint returns an error for reviews with no ingested documents following the `AsyncMock` pattern in `tests/unit/test_review_service.py`.

### Plan
1. Run `make test-unit` first to establish a clean baseline before touching anything.
2. Write the test specification in `tests/unit/test_review_routes.py` before writing any code. This defines what "done" looks like and forces the expected behavior to be precise before implementation. The tests should fail at this point (no validation exists yet).
3. In `create_review_endpoint()` (`api/routes/reviews.py`, line 22), after the `try:` block opens and before the call to `create_review()` on line 36, add a profile lookup and document check:
   - Query the `Profile` by `data.profile_id`, filtered to `user_id == current_user.id` to avoid leaking profile existence to other users.
   - If no profile is found, raise `HTTPException(status_code=404, detail="Profile not found")`.
   - If the profile exists but all three fields (`github_username`, `resume_text`, `portfolio_url`) are `None` or empty string, raise `HTTPException(status_code=422, detail="Profile has no documents to review. Add a GitHub username, resume, or portfolio URL before requesting a review.")`.
4. Run `make test-unit` to confirm the new tests now pass.
5. Run `make check` to confirm lint, formatting, and types are clean.

### Inputs & Outputs
**Endpoint I'm changing:** `POST /reviews` → `create_review_endpoint()` in `api/routes/reviews.py` (line 22)

**Existing behavior (empty profile):**
- Input: `{"profile_id": "<id>"}` where the profile has `github_username=None`, `resume_text=None`, `portfolio_url=None`
- Output: HTTP 200, `status: "pending"` → background task → HTTP 200, `status: "complete"`, three fabricated feedback sections, `overall_score: 0.81`

**New behavior (empty profile):**
- Input: same as above
- Output: HTTP 422, `"Profile has no documents to review..."`. No review record created, no background task queued.

**Test I'll write:**

I'll look at how `test_review_service.py` sets up its `mock_db_session.execute` chain and follow the same pattern.

```python
@pytest.mark.asyncio
async def test_create_review_empty_profile_returns_422(self, mock_db_session):
    """POST /reviews returns 422 when the profile has no ingested documents."""
    empty_profile = Mock()
    empty_profile.id = uuid4()
    empty_profile.user_id = uuid4()
    empty_profile.github_username = None
    empty_profile.resume_text = None
    empty_profile.portfolio_url = None

    # mock db.execute() → scalars().first() → returns empty_profile
    ...

    with pytest.raises(HTTPException) as exc_info:
        await create_review_endpoint(...)
    assert exc_info.value.status_code == 422
```

### Risks & Unknowns
1. **Mocking the DB query inside the route is more involved than mocking the service.** `create_review_endpoint()` will now make two DB calls (profile lookup + `create_review()`). I need to chain `mock_db_session.execute.return_value` correctly for each call. I'll read `test_review_service.py` carefully before writing the test to make sure I follow the existing pattern.
2. **Empty string vs. None.** The model allows `String(255), nullable=True` for `github_username` and `portfolio_url`. A value of `""` is technically not `None` but is also not useful. I'll treat both as empty using `not field or not field.strip()`.
3. **I'm not sure if this check should live in the route or in the service.** The issue references `tests/unit/test_review_routes.py`, so I'll put it in the route for now. If it should live in the service instead, that's a minor refactor.

### Edge Cases
- Profile belongs to a different user: return 404 (same as not found) — do not reveal that the profile exists.
- `github_username` is set to `""` (empty string): treat as no document, return 422.
- One field set, two null (e.g. only `github_username`): accept the request — partial is fine.
- Profile ID in request body does not exist at all: return 404.