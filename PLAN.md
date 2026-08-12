## Solution plan

**Issue:** `POST /reviews` endpoint has no test for when the profile has no ingested documents — https://github.com/ascherj/pathreview/issues/88

### Understand
The `POST /reviews` endpoint (`api/routes/reviews.py`) creates a review with status="pending" and kicks off `process_review` as a background task, regardless of whether the profile has any ingested content. Inside `process_review` (`core/services/review_service.py`), `_run_ingestion_pipeline` correctly returns an empty list when a profile has no `github_username`, `portfolio_url`, or `resume_text`. However, `_run_agent_orchestration` and `_run_rag_retrieval_generation` are placeholder implementations that ignore their `ingestion_results` input entirely and always return hardcoded, fabricated feedback sections and a normal-looking score. As a result, a profile with zero ingested documents still ends up with a review marked "complete" containing fake feedback, rather than a clear error or a "no data to review" signal. Expected behavior: the endpoint (or the background processing) should detect the no-data case and mark the review as failed with a clear reason, instead of fabricating output.

### Map
Files involved:
- `api/routes/reviews.py` — `create_review_endpoint`, the `POST /reviews` handler
- `core/services/review_service.py` — `process_review`, `_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`
- `tests/unit/test_review_service.py` — where the reproduction test and eventual fix-validating test will live

### Plan
1. Add a check in `process_review` (or a new helper) that detects when `ingestion_results` is empty after `_run_ingestion_pipeline` runs.
2. If no sources were ingested, set `review.status = "failed"` with a descriptive log/reason instead of proceeding to `_run_agent_orchestration`.
3. Update `_run_agent_orchestration` and `_run_rag_retrieval_generation` (or skip calling them entirely in the no-data case) so they don't fabricate output when there's nothing to analyze.
4. Add a test asserting that a profile with no ingested sources results in `review.status == "failed"` (replacing/extending the reproduction test that currently documents the buggy "complete" behavior).
5. Manually verify via the running app: create a profile with no GitHub username, portfolio URL, or resume, trigger a review, and confirm it now fails clearly instead of showing fake "complete" feedback on the dashboard.

### Inputs & outputs
**Input:** a `profile_id` for a profile with `github_username=None`, `portfolio_url=None`, `resume_text=None`.
**Output today:** a review with `status="complete"` and fabricated feedback sections.
**Output after fix:** a review with `status="failed"` and no fabricated sections, ideally with a clear reason logged (e.g., "no ingested sources available").

### Risks & unknowns
- Unsure whether "failed" is the correct status to use, or if a new status like "no_data" would be more appropriate — need to check `Review` model and existing status values.
- `_run_agent_orchestration` and `_run_rag_retrieval_generation` are explicitly placeholder functions per their docstrings — unclear if real implementations are already planned elsewhere, which could make this fix obsolete once genuine RAG logic lands.
- Need to confirm how the frontend dashboard displays a "failed" review to make sure the messaging is coherent for users (we saw a "Failed" review status in the UI back in Week 7).

### Edge cases
- Profile has partial data (e.g., only a `portfolio_url` but no GitHub or resume) — should NOT be treated as "no data," since there IS something to analyze.
- Profile fields exist but are empty strings (`""`) rather than `None` — need to confirm `_run_ingestion_pipeline`'s checks handle this correctly.
- Ingestion pipeline itself throws an exception for one source (e.g., GitHub API failure) while others succeed — should still count as "has some data," not "no data."
