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

## Week 8 - Reproduction & Solution Planning

**Reproduction Commit Link:** https://github.com/tam-justin/pathreview/commit/d3a201b97074d8efd10348eea392370d16800b21

**Reproduction Summary:** I reproduced the issue locally using `curl`. I created an empty profile (no resume, no GitHub, and no portfolio) and submitted it for review. The endpoint accepted the request without error and the background task marked the review as "complete" with fabricated placeholder feedback, despite having no ingested documents to analyze.

**Reproduction Steps:**

**Step 1 — Log in and get a token**

```
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=password1"
```

Response (HTTP 200):
```json
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

**Step 2 — Create an empty profile (no resume, no GitHub, no portfolio)**

```
curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_username": null, "portfolio_url": null}'
```

Response (HTTP 200):
```json
{"id":"b3dcdf03-fce6-4314-bb2b-38a4473da433","user_id":"675c7569-cc47-45ee-8071-14fe0422bf70","github_username":null,"portfolio_url":null,"created_at":"2026-07-25T13:11:33.448186Z","resume_filename":null}
```

All three document fields (`github_username`, `portfolio_url`, `resume_filename`) are `null`. There is nothing to analyze.

**Step 3 — Submit a review for the empty profile**

```
curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "b3dcdf03-fce6-4314-bb2b-38a4473da433"}'
```

Response (HTTP 200):
```json
{"id":"68407d92-addf-47ac-b422-58c76ca413e1","profile_id":"b3dcdf03-fce6-4314-bb2b-38a4473da433","status":"pending","sections":null,"overall_score":null,"error_message":null,"created_at":"2026-07-25T13:11:38.774267Z","updated_at":"2026-07-25T13:11:38.774269Z"}
```

The endpoint returned HTTP 200 with `status: "pending"`. No error, no rejection.

**Step 4 — Poll the review after the background task completes**

```
curl -s http://localhost:8000/reviews/68407d92-addf-47ac-b422-58c76ca413e1 \
  -H "Authorization: Bearer $TOKEN"
```

Response (HTTP 200, ~2 seconds later):
```json
{"id":"68407d92-addf-47ac-b422-58c76ca413e1","profile_id":"b3dcdf03-fce6-4314-bb2b-38a4473da433","status":"complete","sections":[{"section_name":"Technical Skills","content":"Detailed feedback on technical skills based on portfolio analysis","confidence":0.85,"suggestions":["Add more detail on AI/ML experience","Include specific technologies and frameworks"]},{"section_name":"Project Experience","content":"Detailed feedback on project experience and impact","confidence":0.8,"suggestions":["Include measurable impact metrics","Add links to project repositories"]},{"section_name":"Career Growth","content":"Feedback on career progression and development","confidence":0.78,"suggestions":["Document learning from each role","Highlight growth in responsibilities"]}],"overall_score":0.81,"error_message":null,"created_at":"2026-07-25T13:11:38.774267Z","updated_at":"2026-07-25T13:11:38.789777Z"}
```

`status` is `"complete"`. The `sections` field contains three detailed feedback sections with confidence scores and suggestions. `overall_score` is `0.81`. None of this came from ingested documents because the profile was empty. This is hardcoded placeholder output from `_run_rag_retrieval_generation()` in `core/services/review_service.py`.

**PLAN.md Link:** https://github.com/tam-justin/pathreview/blob/test/88-reviews-endpoint-missing-documents/PLAN.md

**Blockers or Open Questions:**

## Week 9 - Solution Building & PR Submission

### Check-In 1 (Mid-Week)

**Current Progress:**
I've currently done the following sub-tasks from `PLAN.md`:
- ***Step 1***: I ran `make test-unit` to get a baseline before I touch any of the code. It had 53 failed tests, 375 passed, and 2 warnings. 
- ***Step 2***: I wrote the test specs in `tests/unit/test_review_routes.py`. I wrote a total of six test cases. They cover the following cases: empty profile, profile not found, all fields are empty strings, descriptive error message, ensure empty profiles don't create a review, and a happy path.

**Next Steps:**
For the rest of the week, I'll be working on steps 3, 4, and 5. Steps 3 & 4 add the logic to make sure empty profiles get rejected, a descriptive error message is generated, and the newly added tests pass. Step 5 is to run the linter and formatter to check for clean code.

**Blockers:** N/A

---

### Check-In 2 (End of Week)

**PR Link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What You Built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests Added or Updated:**
[Which test files did you touch? What do they cover?]

**Self-Review Confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR Feedback Received From:** [name or Slack handle, or "none"]