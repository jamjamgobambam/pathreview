## Solution plan

**Issue:** [#88 — `POST /reviews` endpoint has no test for when the profile has no ingested documents](https://github.com/ascherj/pathreview/issues/88)

### Understand

`POST /reviews` is handled by `create_review_endpoint()` in `api/routes/reviews.py` (lines 22–62). It always calls `create_review()` then queues `process_review()` as a background task. There is **no check** that the target profile has anything to review.

`create_review()` in `core/services/review_service.py` (lines 15–32) only builds a `Review` with `status="pending"` and commits it. It does not:
- load the `Profile`
- verify the profile belongs to `current_user`
- check for existing `IngestedSource` rows
- check whether the profile has any ingestible fields (`github_username`, `resume_text`, `portfolio_url`)

Background processing in `_run_ingestion_pipeline()` (lines 197–279) only appends sources when those profile fields are set. If all are missing/empty, it returns `[]`. `_run_agent_orchestration()` (lines 282–304) is a **placeholder** that still returns fake sections even when `ingestion_results` is empty — so the empty path does not currently raise; it can look “successful” with made-up feedback.

There is also **no** `tests/unit/test_review_routes.py` (the file named in the issue). `tests/unit/test_review_service.py` only covers happy-path service helpers — nothing for “profile exists, nothing to ingest.”

**Expected behavior:** `POST /reviews` for a profile that exists but has no content to ingest should return a clear **4xx** error and must **not** create a pending review / start `process_review`.

**Root cause:** Missing precondition validation in the create-review path (`create_review_endpoint` / `create_review`), plus missing route-level test coverage for that path.

### Map

Files I expect to touch:

- `api/routes/reviews.py` — `create_review_endpoint()` (lines 22–62): add validation **before** `create_review()` / `background_tasks.add_task(...)`, raise `HTTPException`, rely on existing `except HTTPException: raise` (lines 54–55).
- `core/services/review_service.py` — either extend `create_review()` (lines 15–32) to load the profile + enforce the empty-content rule, **or** add a small helper (e.g. `assert_profile_ready_for_review`) used by the route. Prefer putting the rule in the service so it stays testable without HTTP.
- `core/models/profile.py` — fields `github_username`, `resume_text`, `portfolio_url` (lines 30–33): these are what `_run_ingestion_pipeline` actually uses.
- `core/models/ingested_source.py` — `IngestedSource` model: useful for understanding “ingested content,” but see Risks — rows are usually created *during* `process_review`, not before `POST`.
- `api/schemas/review.py` — `ReviewCreate` only has `profile_id`; no schema change expected.
- `tests/unit/test_review_routes.py` — **new file** (named by the issue): route test for the empty-content case.
- `tests/unit/test_review_service.py` — existing AsyncMock / `@pytest.mark.unit` / `@pytest.mark.asyncio` patterns to mirror (e.g. `test_create_review_returns_review_with_pending_status` around line 48).

### Inputs & outputs

**Endpoint:** `POST /reviews`  
**Handler:** `create_review_endpoint(data: ReviewCreate, ...)`  
**Body:** `{ "profile_id": "<uuid>" }`

**Existing happy path (keep working):**
- Input: authenticated user + owned profile that has at least one of `github_username` / `resume_text` / `portfolio_url`
- Output: `200` + `ReviewResponse` with `status="pending"`; `process_review` is queued

**New behavior (empty content case):**
- Input: authenticated user + owned profile where `github_username`, `resume_text`, and `portfolio_url` are all missing/empty (nothing `_run_ingestion_pipeline` can ingest)
- Expected output: `HTTP 400` with detail like `"Profile has no ingested content to review"` (exact string locked in the test)
- Does **not** call `db.add(Review)` / does **not** queue `process_review`

**Status-code choice:** Use **400** (bad request / invalid state for this operation), matching client-error style in `api/routes/auth.py` (e.g. email-already-registered). **404** stays reserved for “profile not found / not owned,” same pattern as `get_profile_endpoint` in `api/routes/profiles.py` (lines 130–133).

**Test I'll write** (in new `tests/unit/test_review_routes.py`):

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_profile_with_no_ingested_content_returns_400():
    """POST /reviews should return 400 when the profile has nothing to ingest."""
    # Arrange: authenticated user; profile exists and is owned; all ingestible fields empty;
    # override get_current_user + get_db / service deps as needed (no route-test helpers exist yet).

    response = await client.post(
        "/reviews",
        json={"profile_id": str(empty_profile.id)},
        headers={"Authorization": "Bearer ..."},
    )

    assert response.status_code == 400
    assert "no ingested content" in response.json()["detail"].lower()
```

I'll follow FastAPI `dependency_overrides` for `get_current_user` / `get_db`, and match pytest markers from `test_review_service.py`. If pure route testing is too heavy for Tier 1, fall back to a service-level test that asserts `create_review` (or the new helper) raises `HTTPException(400)` for an empty profile — still add `test_review_routes.py` as the issue asks, even if thin and calling the endpoint function with mocks.

### Plan

1. Confirm empty-content definition against the live flow: at `POST` time, `IngestedSource` rows usually do **not** exist yet because ingestion runs inside `process_review` (`review_service.py` ~127–128). So the precondition should be “profile has no ingestible fields,” not “zero `IngestedSource` rows.” Update this plan if investigation proves reviews are only created after a separate ingest step.
2. Add profile lookup + ownership check if missing (today `create_review` ignores `user_id` entirely). Reuse the same ownership idea as `get_review()` / `get_profile()` — unknown profile or wrong owner → **404** `"Profile not found"`.
3. Add empty-content check after the profile is loaded: if not (`github_username` or `resume_text` or `portfolio_url`), raise `HTTPException(status_code=400, detail="Profile has no ingested content to review")` **before** creating the `Review`.
4. Wire that raise so `create_review_endpoint` surfaces it via the existing `except HTTPException: raise` block (lines 54–55) — do not let it fall into the generic 500 handler (lines 56–62).
5. Create `tests/unit/test_review_routes.py` with the test drafted above (and optionally a happy-path smoke assert if cheap).
6. Run `make test-unit` focusing on the new file, then full unit suite.
7. Run `make check` (lint / format / types) before PR week.

### Risks & unknowns

1. **“Ingested content” vs ingestible profile fields.** The issue says “no associated ingested content,” which sounds like `IngestedSource` rows — but those are written *during* `_run_ingestion_pipeline`, after `POST` already returned `pending`. Checking row count at `POST` would reject almost every first review. I’ll treat empty ingestible profile fields as the intended signal unless the product flow shows a prior ingest API.
2. **No route tests exist in this repo.** There is no `tests/unit/test_*routes*.py` to copy. Building FastAPI `TestClient` / `AsyncClient` + `dependency_overrides` is new ground here — risk of a flaky or overbuilt test. Mitigation: start from how `api/main.py` mounts routers and how `get_current_user` is defined in `api/middleware/auth.py`.
3. **`create_review` currently ignores `user_id`.** Adding ownership + empty checks changes more than “just a test.” Stay minimal: only what’s required for a correct 400/404 contract.
4. **Placeholder agent hides the bug.** `_run_agent_orchestration` returns fake sections even when `ingestion_results == []`, so a live empty profile may not “crash” today — it fails silently with nonsense output. The explicit 400 is what makes the behavior correct and testable.
5. **`IngestedSource(...)` in `_run_ingestion_pipeline` passes `raw_data=...`, but `core/models/ingested_source.py` has no `raw_data` column.** That’s outside #88 scope, but it means I should not rely on that path for the empty-content test setup.

### Edge cases

- Profile missing or not owned by caller → **404** `"Profile not found"` (same as profiles route); distinct from empty-content **400**
- Profile with only `github_username` set (resume/portfolio null) → **allowed** (happy path); ingestion has something to run
- Profile with whitespace-only `resume_text` → treat as empty (use `.strip()`); should **400**
- Profile that already has `IngestedSource` rows from a prior run but cleared profile fields → still **400** under the field-based rule (document; don’t special-case unless product requires it)
- Unauthenticated request → still **401** from auth middleware; don’t break `get_current_user` when overriding deps in tests
