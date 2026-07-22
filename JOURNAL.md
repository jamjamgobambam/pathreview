## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/86)

**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses
 #86

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Tier Reasoning:**
I have contributed to open source projects before and have some familiarity with APIs. Due to this, I belive that the Tier 2 issues with tags referencing "api" will be a good fit for me. I can commit to the 8-12 hour time commitment that is expected for a Tier 2 issue.

**Problem summary:**
Currently the API rate limiter throws a 429 error when the client has exceeded their limit. However, the client doesn't know how many requests they have left before hitting or exceeding the limit, making it difficult to navigate and use the API. A successful fix will add "limit" and "remaining" headers to each response that the client recieves from the API. The relevant direcotry and file for this fix are api/middleware/ and safety/rate_limiter.py.

**Branch name:** feat/86-add-rate-limit-header

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅ ] Issue added to cohort ledger