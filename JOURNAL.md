## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/32

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1 [ x ] Tier 2 [ ] Tier 3
I have contributed to larger codebases before and feel tier 2 level issue will be achievable. I also will be able to commit to the time level suggested on the issue of 4-7 hours.

**Problem summary:**
If the same profile gets submitted with no changes to its porfolio information, then it still gets re-reviewed and executes the full RAG pipeline. This issue affects the core review service and utilizes the rag review generator service. Currently, there are no checks to see if profiles are identical and no way to flag if profile has been seen before. A succesful fix would create a hash to represent the profile's porfolio information and check if the new profile submitted matches any existing profile's that have been reviewed. Otherwise, it will kick-off the full RAG pipeline to create a review.

**Branch name:** feat/32-cache-repeated-portfolio-queries

**Setup confirmation:** [ x ] App runs locally at localhost:5173

**Cohort ledger:** [ x ] Issue added to cohort ledger
I checked the issue count and am confortable with the number of other people working on this issue.

## Implementation Checklist

### Part 1 — Understanding the Issue

- Same profile submitted twice without changes currently re-runs full RAG pipeline
- Need to detect when portfolio content hasn't changed and reuse existing review
- Implementation: create content hash from profile data (github_username + resume_text + portfolio_url) and cache reviews by this hash
- core/models/profile.py — Profile model
- core/services/review_service.py — Review processing logic
- rag/generator/review_generator.py — RAG pipeline
- api/schemas/review.py — Review schema
- Before: User submits same portfolio twice → system re-runs full pipeline both times
- After: User submits same portfolio twice → system returns cached review from first submission
- Success metric: When identical profile submitted, retrieve existing review without re-processing

### Part 2 — Tier Fit

- I reviewed the interactions between the Profile model, review_service, and review_generator
- Involves adding caching logic to multiple layers such as database query, and service function

### Part 3 — Codebase Readiness

- The `_run_ingestion_pipeline()` is operation called for every new review and the caching will hopefully help prevent running this time consuming operation
- Profile model stores: github_username, resume_text, portfolio_url
- Review model stores: profile_id, status, sections, overall_score
- Plan: Add `content_hash` to data model, calculate hash, and check for existing review before pipeline
- The tests/unit/ or tests/ for relevant Profile and Review related tests that will need to modified to account for this new data point

### Part 4 — Scope and Time

- Checked issue comments and cohort ledger
- Comfortable with current number of claims
- Estimated 4-7 hours for this Tier 2 issue
- Can complete before Week 9 deadline

## Week 8 — Reproduction & solution planning

**Steps to reproduce**

1. launch service: $ make run
2. create new user: click on register

```
2026-07-21 18:20:41 [info     ] user_registered                email=user1@gmail.com request_id=c729f0f7-8df5-4050-b68b-8b4f88e0b6ec user_id=ef04b23b-45cd-4bdb-a947-9552591ca746
INFO:     127.0.0.1:49657 - "POST /auth/register HTTP/1.1" 200 OK
```

3. create a review: click on start a new review

- input: github: user1, resume: resume template pdf found online, portfolio url: https://user1.com

4. observed in terminal logs that POST /reviews and observed the the RAG pipeline was invoked in the terminal logs:

```
2026-07-21 18:24:18 [info     ] review_created                 profile_id=32141eab-51c7-4787-9f1f-31f24137c91d request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212 user_id=ef04b23b-45cd-4bdb-a947-9552591ca746
INFO:     127.0.0.1:50221 - "POST /reviews HTTP/1.1" 200 OK


2026-07-21 18:24:18 [info     ] review_processing_started      profile_id=32141eab-51c7-4787-9f1f-31f24137c91d request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212
2026-07-21 18:24:18 [error    ] github_ingestion_failed        error="'raw_data' is an invalid keyword argument for IngestedSource" request_id=995e121f-8690-4243-a00c-0ca85e3ae361 username=user1
2026-07-21 18:24:18 [error    ] portfolio_ingestion_failed     error="'raw_data' is an invalid keyword argument for IngestedSource" request_id=995e121f-8690-4243-a00c-0ca85e3ae361 url=https://user1.com
2026-07-21 18:24:18 [info     ] ingestion_pipeline_completed   request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212 sources_count=2
2026-07-21 18:24:18 [info     ] agent_orchestration_completed  request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212 sections_count=2
2026-07-21 18:24:18 [info     ] rag_retrieval_completed        request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212
2026-07-21 18:24:18 [info     ] safety_checks_passed           request_id=995e121f-8690-4243-a00c-0ca85e3ae361


2026-07-21 18:24:18 [info     ] review_processing_completed    overall_score=0.81 request_id=995e121f-8690-4243-a00c-0ca85e3ae361 review_id=19165315-2b3b-4c8c-8b37-92915c0da212
```

5. repeated steps 3 and 4 with the same input I listed
6. confirmed that the RAG pipeline was re-run and a second review was created in the terminal logs:

```
2026-07-21 18:24:51 [info     ] review_created                 profile_id=378840d5-8e24-4dac-95f7-259baf0dd651 request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5 user_id=ef04b23b-45cd-4bdb-a947-9552591ca746
INFO:     127.0.0.1:50248 - "POST /reviews HTTP/1.1" 200 OK


2026-07-21 18:24:51 [info     ] review_processing_started      profile_id=378840d5-8e24-4dac-95f7-259baf0dd651 request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5
2026-07-21 18:24:51 [error    ] github_ingestion_failed        error="'raw_data' is an invalid keyword argument for IngestedSource" request_id=3e4018da-c780-4049-aba6-7cc8282d4387 username=user1
2026-07-21 18:24:51 [error    ] portfolio_ingestion_failed     error="'raw_data' is an invalid keyword argument for IngestedSource" request_id=3e4018da-c780-4049-aba6-7cc8282d4387 url=https://user1.com
2026-07-21 18:24:51 [info     ] ingestion_pipeline_completed   request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5 sources_count=2
2026-07-21 18:24:51 [info     ] agent_orchestration_completed  request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5 sections_count=2
2026-07-21 18:24:51 [info     ] rag_retrieval_completed        request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5
2026-07-21 18:24:51 [info     ] safety_checks_passed           request_id=3e4018da-c780-4049-aba6-7cc8282d4387


2026-07-21 18:24:51 [info     ] review_processing_completed    overall_score=0.81 request_id=3e4018da-c780-4049-aba6-7cc8282d4387 review_id=daa4bfe3-a07c-46f0-a9d5-3b63f690bda5
```

**Reproduction commit link:** https://github.com/priyalpatell/pathreview/commit/c0b67afe5b20c6eed9227392450a7f7a497aba05

**Reproduction summary:**
I reproduced the issue by making 2 reviews using the same user and portfolio. In the logs, I observed that the RAG pipeline was ran for both runs, highlighting the need to caching to reduce these repetitive operations.

**PLAN.md link:** https://github.com/priyalpatell/pathreview/blob/feat/32-cache-repeated-portfolio-queries/PLAN.md

**Blockers or open questions:**
None for now

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented the full caching service and completed all tasks in PLAN.md. The appropriate edits to the POST /review and review create service function.

**Next steps:**
I will be opening my PR and making appropriate edits based on the feedback.

**Blockers:**
Nothing so far - resolved linter issues I was originally facing.
