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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [962e503](https://github.com/asnts18/pathreview/commit/962e503)

**Reproduction summary:**
Created a fresh user, then a profile with no `github_username`, `portfolio_url`, or `resume_text` set, then triggered `POST /reviews` against it. The review reached `status: "complete"` with a fabricated `overall_score: 0.81` and three canned feedback sections, instead of failing — confirming that `process_review()` never checks whether ingestion actually produced anything before generating feedback.

**PLAN.md link:** [PLAN.md](https://github.com/asnts18/pathreview/blob/test/88-review-endpoint-test/PLAN.md)

**Blockers or open questions:**
Still deciding whether "no documents ingested" should be judged from the profile's own fields (`github_username`/`portfolio_url`/`resume_text`) or from the `ingested_sources` table directly — these should normally agree, but could diverge if a profile has stale `IngestedSource` rows from a prior partial run. See Risks & unknowns in `PLAN.md` for details.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md` step 1: `process_review()` in `core/services/review_service.py` now checks whether `_run_ingestion_pipeline()` returned any results, and if not, sets `status="failed"` with a descriptive `error_message` instead of continuing on to the placeholder agent/RAG/safety steps. Also completed step 2 — confirmed `error_message` is already exposed on `ReviewResponse` for `GET /reviews/{id}`, and added it to the lighter `GET /reviews/{id}/status` payload too, since that's the endpoint clients poll while a review is processing. Wrote both regression tests from steps 3–4 in `tests/unit/test_review_service.py`: one asserting a documentless profile ends in `status="failed"` with a non-null `error_message`, and a companion happy-path test asserting a profile with at least one source still reaches `status="complete"`. Re-ran the original curl reproduction from Week 8 against a live local server (Postgres via `docker compose up -d`) — confirmed the same profile shape now returns `status: "failed"` with the descriptive message on both endpoints, and confirmed a profile with `github_username` set is unaffected and still completes normally.

Resolved the open question from Week 8: went with checking `_run_ingestion_pipeline()`'s return value (the profile's own fields) rather than querying `ingested_sources` directly, since that function is the sole writer of those rows and is already re-run fresh on every `process_review()` call.

Verified no regressions: `make test-unit` still shows the same 53 pre-existing failures (all pre-existing mock-configuration bugs in unrelated test files) plus 377 passing (up from 375 — the 2 new tests). `make lint` (182 errors) and `make typecheck` (103 errors) are both unchanged from the pre-existing baseline I recorded before starting.

**Next steps:**
Finish filling out the PR template, double-check branch name and commit messages against `docs/CONTRIBUTING.md` conventions, and open the PR.

**Blockers:**
None.