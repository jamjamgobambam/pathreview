# pathreview - JOURNAL.md

## Week 7 — Issue selection

**Issue Link:** https://github.com/ascherj/pathreview/issues/88

**Issue Title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem Summary:**
The `POST /reviews` endpoint in `api/routes/reviews.py` accepts review requests for any profile, including ones with no ingested documents (resume, GitHub profile, portfolio). When that happens, the background task `process_review` in `core/services/review_service.py` runs the ingestion pipeline with no documents to process. This could silently produce empty output or crash without a clean error. The test suite in `tests/unit` covers basic review creation and retrieval but has no test for this edge case. A successful fix adds an input validation check that rejects profiles with no ingested documents, and adds a test in a new `tests/unit/test_review_routes.py` that confirms the endpoint returns a meaningful error (HTTP 422 or 400) rather than accepting the request and letting it fail silently in the background.

**Scope Reasoning:**

***Part 1 - Understanding the Issue***

[x] *Requirement*: I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.

The problem is that `POST /reviews` never checks if a profile submitted for review actually has any documents for ingestion before creating the review. This leads to a silent failure. The expected behavior is that the endpoint rejects the empty profile before attempting to create the review.

[x] *Requirement*: I've located the relevant files and confirmed they exist in the codebase.

The relevant files in the codebase for this issue are: `api/routes/reviews.py` which contains the `POST /reviews` endpoint and `core/services/review_service.py` which contains `create_review()` and `process_review()` which handle the review logic. 

[x] *Requirement*: I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

Before: A user calls `POST /reviews` for a profile with no ingested documents. The endpoint accepts it and returns HTTP 201 with `status: "pending"`. The background task runs and returns an entirely fake "completed" review because our current logic is filled with placeholders. The fact that the profile is empty is entirely ignored.

After: The endpoint checks that the profile has at least one ingested document before creating the review. If there are none, it immediately returns HTTP 422 or 400 with a clear error message. No review record is created, no background task runs, and the user gets clear actionable feedback.

***Part 2 - Tier Fit***

[x] *Requirement*: If this is my first open source contribution: I'm choosing Tier 1.

This is my first open source contribution so I am choosing a Tier 1 issue. On the `pathreview` repo, this issue has the `tier-1` and `good first issue` labels. The issue itself also matches up with the expected scope for a Tier 1 issue (bug fix, missing validation, missing test, etc).

***Part 3 - Codebase Readiness***

[x] *Requirement:* I've found and read the specific code the issue references (not just the file — the function or section).

I've found and read the relevant functions for this issue:
- `create_review_endpoint()` in `api/routes/reviews.py` 
- `process_review()` in `core/services/review_service.py`
- `_run_ingestion_pipeline()` in `core/services/review_service.py`
- `_run_agent_orchestration()` in `core/services/review_service.py`
- `_run_rag_retrieval_generation()` in `core/services/review_service.py`
- `_run_safety_checks()` in `core/services/review_service.py`

[x] *Requirement:* I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.

The rough plan is to add a validation check in `create_review_endpoint()` that rejects the request if the profile has no documents for ingestion. 

[x] *Requirement:* I've found the test file for my module and read at least one test end-to-end.

The current test suite has no test file for this endpoint. This is exactly what the issue is referencing. Instead, I read `tests/unit/test_review_service.py` which contains tests for creating reviews, getting a review, and listing reviews. It covers the happy path for the service, but contains nothing for error cases.

***Part 4 - Scope and Time***

[x] *Requirement:* I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

At the time of writing, this issue has been claimed by 10 people total (including me) according to the ledger's catalog. I'm okay with how many others are working on this issue.

[x] *Requirement:* I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.

This is a Tier 1 issue, which according to the checklist, should take 3-6 hours of focused work. In addition, the issue description estimates 2-3 hours of effort. This is perfectly completable before the Week 9 deadline (2 weeks away).

[x] *Requirement:* This issue has no open blockers or dependencies on other unresolved issues.

At the time of writing, there are no open blockers or dependencies on other unresolved issues mentioned anywhere on the issue page. 

**Branch Name:** test/88-reviews-endpoint-missing-documents

**Setup Confirmation:** [x] App runs locally at localhost:5173

**Cohort Ledger:** [x] Issue added to cohort ledger