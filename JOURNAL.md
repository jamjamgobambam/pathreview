## Week 7 — Issue selection

**Issue link:** [[paste link here]](https://github.com/ascherj/pathreview/issues/88)

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents #88

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The /reviews endpoint currently assumes a profile will already have some documents ingested before a review is requested, and that assumption is never checked in the test suite. If someone triggers a review for a profile that exists but hasn't had anything ingested yet, it's unclear whether the endpoint fails gracefully or throws an unhandled exception, since no test exists to pin down the expected behavior. This is a gap in edge-case coverage rather than a confirmed bug — the fix is really about writing a regression test that calls the endpoint under this specific condition and asserts a clean, well-formed error response (e.g. a 4xx with a descriptive message) instead of a server crash. A successful fix gives the team confidence that this edge case is handled predictably and prevents future changes from silently reintroducing a crash for profiles with no ingested content.

**Branch name:** test/88-review-endpoint-test

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Reproduction steps:**

Root cause traced to `process_review()` in [core/services/review_service.py:82](core/services/review_service.py#L82). `POST /reviews` ([api/routes/reviews.py:22](api/routes/reviews.py#L22)) never checks for ingested documents — it creates the review with `status="pending"` and hands the real work to a background task. Inside that task, `_run_ingestion_pipeline()` ([core/services/review_service.py:197](core/services/review_service.py#L197)) correctly returns `[]` when a profile has no `github_username`, `portfolio_url`, or `resume_text`. But `_run_agent_orchestration()` ([:282](core/services/review_service.py#L282)) and `_run_rag_retrieval_generation()` ([:307](core/services/review_service.py#L307)) are hardcoded placeholders that ignore the (empty) ingestion results entirely, and `_run_safety_checks()` ([:357](core/services/review_service.py#L357)) only validates shape, not provenance. Net effect: **no crash, no 4xx** — a documentless profile silently reaches `status="complete"` with fabricated feedback.

Steps to reproduce against a local server (`make run`, API at `localhost:8000`):

1. Register a fresh user:
   ```bash
   curl -s -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "empty-profile-test@example.com", "password": "testpass123"}'
   ```
   Extract `access_token` as `$TOKEN`.

2. Create a profile with no fields set (all optional per `ProfileCreate`):
   ```bash
   curl -s -X POST http://localhost:8000/profiles -H "Authorization: Bearer $TOKEN"
   ```
   Confirmed profile `349cc633-fc7a-4178-9207-7283dab27943` created with `github_username`, `portfolio_url`, `resume_text` all null and zero `ingested_sources` rows.

3. Trigger a review for that profile:
   ```bash
   curl -s -X POST http://localhost:8000/reviews \
     -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"profile_id": "349cc633-fc7a-4178-9207-7283dab27943"}'
   ```
   Returns `201` with `status: "pending"`, review id `72a8a928-ed09-43be-879e-128bc03e142f`.

4. Poll the review after the background task runs:
   ```bash
   curl -s http://localhost:8000/reviews/72a8a928-ed09-43be-879e-128bc03e142f -H "Authorization: Bearer $TOKEN"
   ```
   **Actual result:** `status: "complete"`, `overall_score: 0.81`, `error_message: null`, and three fully-populated feedback sections ("Technical Skills", "Project Experience", "Career Growth") — none of which reflect real analysis, since nothing was ever ingested.

**Expected behavior (not yet implemented):** the review should end in `status="failed"` with a descriptive `error_message` (the column already exists on `Review` but is never set on this path), rather than fabricating a successful result. No test currently exists for this path (`process_review`, `_run_ingestion_pipeline`, and this scenario are entirely uncovered in `tests/unit/test_review_service.py`).