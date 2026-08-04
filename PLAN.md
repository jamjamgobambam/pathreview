## Solution plan

**Issue:** [issue title and link]
Add integration tests for authentication edge cases #90: https://github.com/ascherj/pathreview/issues/90

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
There are tests to be added to make sure the authentication is working properly and there's no unauthorized attack happen. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The files involved:
- frontend/src/services/api.ts:9: builds the frontend for login and register and sends the collected data to the backend--api/routes/auth.py--for authentication.
- api/routes/auth.py: routes the public /auth/register and /auth/login endpoints that verify credentials and issue JWT tokens.
- core/security.py: provides the low-level cryptographic password hashing/verification and JWT creation/decoding.
- api/middleware/auth.py: validates the JWT authentication token for subsequent access to protected routes and resolving it to the current User or raising 401. 

I will add tests to make sure the functions login and register functions in routes/auth.py, get_current_user function is middleware/api.pu, and hash_password, verify_password, create_access_token, and decode_access_token in security.py is doing what it's supposed to do.


### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

These are the tests cases:
Case 1: Authenticate with expired token 
Case 2: Signed with a different secret than the username and password
Case 3: Invalid JWT string (random string or wrong segment count) 
Case 4: A request has no authorization header 
Case 5: Bearer with missing token
Case 6: Authorization token with no bearer prefix
Case 7: Multiple arguments after Bearer like 'Bearer a b' 

[] I would create tests for each of the cases to make sure they are working as intended


### Inputs & outputs
What does your fix take as input? What should it produce or change?

It should test to make sure the authentication is secured against potential unauthorized breach. My fix doesn't take any input; in fact, it's not even a fix. It adds tests for authentication. 

### Risks & unknowns
What could go wrong? What are you still unsure about?

There could still be unknown vulnerability that may lead to unauthorized access. 

### Edge cases
What inputs or states should your fix handle gracefully?

An unauthorized access should be given a warning without giving away any sensitive information, for example, if someone tries to login with a forged signature, it would raise an error without giving away the user details. 

Also, if username and password is wrong, they should just receive invalid username or password message on the screen. However, we can limit how many times a user with the same email can attempt entering passwords to prevent password stuffing or dictionary attack. 