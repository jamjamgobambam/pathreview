## Solution plan

**Issue:** [issue title and link]
Add integration tests for authentication edge cases #90: https://github.com/ascherj/pathreview/issues/90

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
There are tests to be added to make sure the authentication is working properly and there's no unauthorized attack happen. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- core/security.py: provides the low-level cryptographic password hashing/verification and JWT creation/decoding.
- api/middleware/auth.py: verify authentication on protected routes by validating the request's JWT and resolving it to the current User or raising 401. 
- api/routes/auth.py: routes the public /auth/register and /auth/login endpoints that verify credentials and issue JWT tokens.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

[] I would create tests for eac of the cases


### Inputs & outputs
What does your fix take as input? What should it produce or change?
It should test to make sure the authentication is secured. 

### Risks & unknowns
What could go wrong? What are you still unsure about?
There could still be unknown vulnerability that may affect it. 

### Edge cases
What inputs or states should your fix handle gracefully?

Case 1: Authenticate with expired token should return 401 error
Case 2: A request no authorization header 
Case 3: Bearer with missing token
Case 4: Authorization token with no bearer prefix
Case 5: Multiple arguments after Bearer like 'Bearer a b'
Case 6: Invalid JWT string (random string or wrong segment count)  
Case 7: Signed with a different secret than the username and password