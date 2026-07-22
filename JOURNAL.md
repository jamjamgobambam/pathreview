## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases #90

**Tier:**  [ ] Tier 2  

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The auth middleware is tested with a valid token but there are no tests for: expired tokens, malformed tokens, missing Authorization header, and tokens signed with a different secret.

The issue affects the authentication middleware, and it needs to be thoroughly tested for potential security issues, such as expired tokens, malformed tokens, missing Authorization header, and tokens signed with a different secret. A successful fix would patch any known authentication vulnerability and making sure no unauthorized access occur. 

Relevant file: tests/integration/test_auth_middleware.py

**Branch name:** test/90-add-tests-authentication

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger 