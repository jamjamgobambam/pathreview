## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**
I selected this Tier 1 issue because I am comfortable writing focused unit tests but am still becoming familiar with the project's review API and error-handling flow. The change has a narrow scope in one test file, making it a manageable way to learn how the endpoint handles profiles and ingested content.

**Problem summary:**
The unit tests for the review routes do not cover the case where a valid profile exists but has no associated ingested content. As a result, a regression could cause the `POST /reviews` endpoint to crash instead of returning a controlled error response. The missing coverage belongs in `tests/unit/test_review_routes.py` and should exercise this empty-content condition. A successful change will verify that the endpoint responds with an appropriate error status and message when there is nothing available to review.

**Branch name:** `tests/88-POST-/reviews-endpoint-has-no-test-for-when-the-profile-has-no-ingested-documents-`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I created a valid profile without a résumé, GitHub username, portfolio URL, or ingested sources, then submitted `POST /reviews` using that profile’s ID. The endpoint incorrectly returns a pending review instead of a controlled 4xx error indicating there is no content to review.

To reproduce the error I submitted 
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyZGJiNDRlNi01N2M1LTQyYTktYWJlNy1mN2IxMjQxZjYwNTAiLCJleHAiOjE3ODQ4NTk0Mzl9.7K5caMJ4nljB5_QH35YcsrpYCGVlAQYIVCR1utQ6xmc",
  "token_type": "bearer"
}

{
  "id": "5a312eb8-1744-40f1-aa77-e773c3c27f39",
  "user_id": "2dbb44e6-57c5-42a9-abe7-f7b1241f6050",
  "github_username": "string",
  "portfolio_url": "string",
  "created_at": "2026-07-24T06:19:15.677525Z",
  "resume_filename": null
}

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
