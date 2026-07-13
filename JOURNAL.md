# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/84

**Issue title:** Add pagination to GET /reviews list endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue asks for `page` and `page_size` query params on `GET /reviews` so users with a lot of reviews don't get one huge response back. When I actually looked at the code though, that part was already built — `api/routes/reviews.py` and `core/services/review_service.py` already had page/page_size, offset/limit, and a default page size of 20. What was still broken was how the total count got calculated: it was pulling every matching review row into memory and taking `len()` of the list instead of asking Postgres for an actual count. So even though the response itself was paginated, the server was still doing a full scan of that user's reviews on every single request, which is basically the same performance problem the issue was trying to prevent. I scoped my fix down to that — swap the count query over to SQL's `COUNT()` instead of loading every row.

**Scope notes:**
Went through the "is this right for me" checklist before committing to it — it's tagged tier-1 and good first issue, the change lives in one file, and I could actually verify it worked end to end by logging in through the running app and hitting the endpoint with a real token instead of just eyeballing the code. The one thing that made me pause was realizing the issue as literally written was already resolved in the codebase — I tested it against the live app before assuming there was nothing left to do, and that's how I found the count-query issue underneath it.

**Branch name:** perf/84-reviews-count-query

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** n/a Done as TF assignment
