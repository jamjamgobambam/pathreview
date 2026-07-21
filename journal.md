## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents
 

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3
**Scope Reasoning**
[is this right for me?]
The issue is understandable, the reasoning behind it,as to why the review feature would be required, The consequences of not fixing it and what a successful fix looks like are all clear and explained clearly. The surrounding context and related file have been accessed.
The ideal fix has been decided.

**Problem summary:**
The POST /reviews endpoint has no test covering the case where a profile has no ingested documents. Right now, calling this endpoint for such a profile likely causes an unhandled error rather than a clean, expected response. A successful fix adds a check for whether a profile has associated ingested content, returns a proper error response (rather than crashing) when it doesn't, and includes a test verifying this behavior.
**Branch name:** 
fix/88-no-profile-associated-ingested-content-review-endpoint

**Setup confirmation:** [Yes ] App runs locally at localhost:5173

**Cohort ledger:** [ Yes] Issue added to cohort ledger