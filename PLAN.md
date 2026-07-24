# Solution plan

**Issue:** POST /reviews endpoint has no test for when the profile has no
ingested documents — https://github.com/ascherj/pathreview/issues/88

## Understand

**Root cause:** `create_review_endpoint` accepts a review request without ever
checking that the profile has anything to review. When a profile has no GitHub
username, résumé, or portfolio URL, `_run_ingestion_pipeline` skips all three
branches and returns an empty source list — but the downstream `_run_agent_
orchestration` and `_run_rag_retrieval_generation` steps ignore the ingestion
result and return hardcoded placeholder feedback, so `_run_safety_checks` passes
and the review is marked "complete". No test covers this case today.

**Expected vs. actual:**
- *Expected:* requesting a review for a content-less profile returns a clear 4xx
  error (422) explaining there is nothing to review.
- *Actual:* the endpoint returns HTTP 200 with `status: "pending"`, and the
  review later completes with generic feedback unrelated to the (absent) content.

## Map

**Involved (read to understand):**
- `api/routes/reviews.py` — `create_review_endpoint` (the endpoint under test)
- `core/services/review_service.py` — `create_review`, `process_review`,
  `_run_ingestion_pipeline` (where "content" is / isn't produced)
- `core/models/profile.py`, `core/models/ingested_source.py` — what "content" means
- `api/routes/profiles.py` — existing 404/422 pattern to mirror (`:50`, `:130`)
- `tests/unit/test_review_service.py` — reference for fixture/mock/assert style

**Files I expect to touch:**
1. `tests/unit/test_review_routes.py` — NEW; the test (primary deliverable)
2. `api/routes/reviews.py` — add the no-content validation
3. `tests/conftest.py` — possibly add a shared TestClient / fake-auth fixture

## Plan

1. **Define "no content".** Treat a profile as having no content when
   `github_username`, `resume_text`, and `portfolio_url` are all empty. (Ingested
   rows are created only during processing, so they're always 0 before the first
   review — the profile's own source fields are the right synchronous signal.)
2. **Add validation in `create_review_endpoint`,** before
   `background_tasks.add_task(...)`: load the profile and, if it has no content,
   `raise HTTPException(422, "Profile has no content to review")` — mirroring the
   422 pattern already used in `create_profile_endpoint`.
3. **Write `tests/unit/test_review_routes.py`** using FastAPI's `TestClient` with
   `app.dependency_overrides` to fake `get_current_user` and `get_db`; assert that
   `POST /reviews` for a content-less profile returns 422.
4. **Add a contrast test:** a profile *with* content still returns 200 / "pending",
   proving the check doesn't over-reject.
5. **Verify:** run `make test-unit` (green), then `make lint` / `make typecheck`.

## Inputs & outputs

- **Input:** an authenticated `POST /reviews` whose `profile_id` points at a
  profile with no source content.
- **Output / change:** the endpoint returns **422** with a clear message instead
  of 200 "pending"; no `Review` row is created for such a request. Profiles that
  *do* have content are unaffected (still 200 "pending"). A new unit test locks in
  both behaviors.

## Risks & unknowns

- **Status code:** choosing 422 to match the résumé-validation precedent; a
  reviewer might prefer 400. Low risk, easy to change.
- **"No content" definition:** using the profile's source fields rather than
  `IngestedSource` rows; need to confirm this matches the issue's intent.
- **Profile existence/ownership:** `create_review` currently never checks the
  profile exists or belongs to the user. Loading it for the content check invites
  a 404 too — I'll scope this to the 422 case and note 404 as a follow-up to avoid
  scope creep.
- **First endpoint test in the repo:** no existing `TestClient` example, so I'm
  establishing the pattern (sync client, dependency overrides) — small learning risk.
- **Pre-existing bugs nearby** (`IngestedSource(raw_data=...)` invalid kwarg;
  passing a request-scoped DB session into a background task) are out of scope but
  may surface while testing.

## Edge cases the fix should handle

- Profile with all source fields empty → **422** (target case).
- Profile with just one source (e.g. only `github_username`) → **allowed**, 200.
- Valid profile with content → **200 "pending"** (unchanged).
- Missing/invalid auth → **401** (already handled by `get_current_user`).
- Nonexistent or not-owned `profile_id` → ideally **404** (currently unhandled;
  flagged as out-of-scope follow-up).
