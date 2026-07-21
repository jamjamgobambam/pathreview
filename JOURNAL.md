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
