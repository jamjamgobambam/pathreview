## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/86)

**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses
 #86

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Tier Reasoning:**
I have contributed to open source projects before and have some familiarity with APIs. Due to this, I believe that the Tier 2 issues with tags referencing "api" will be a good fit for me. I can commit to the 8-12 hour time commitment that is expected for a Tier 2 issue.

**Problem summary:**
Currently the API rate limiter throws a 429 error when the client has exceeded their limit. However, the client doesn't know how many requests they have left before hitting or exceeding the limit, making it difficult to navigate and use the API. A successful fix will add "limit" and "remaining" headers to each response that the client receives from the API. The relevant directory and file for this fix are api/middleware/ and safety/rate_limiter.py.

**Branch name:** feat/86-add-rate-limit-header

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ddingi09/pathreview/commit/9d2a2d30f20fc1678a59176b75c0dfea15e63a77)

**Reproduction summary:**
As this issue is a feat, not a fix, in order to reproduce the issue I read through each of the files in the api/middleware directory and the safety/rate_limiter.py file. I asked Claude to explain how these files interact with each other and how the current rate limit route is constructed. I found that currently a 429 error is not thrown anywhere in the repo, this will be a feature that I will implement following the established error structure in api/middleware/auth.py. Additionally, rate_limiter.py currently computes the requests that the user has left. I can use this number as a header in the updated return statement. I will add the two new headers as a new api/middleware file and register them in api/main.py following the structure of request_id.py.

**PLAN.md link:** (https://github.com/ddingi09/pathreview/blob/feat/86-add-rate-limit-header/PLAN.md)

**Blockers or open questions:**