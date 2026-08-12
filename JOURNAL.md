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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

Before creating tests I created a test account to check how the authentication works for any issue reproduction. 

### Case 1: Authenticate with expired token should return 401 error
Login with expire token:
As I tried to reproduce signing with expired token, I came across a potential issue where a user logout, but the authentication token stays valid until the expired time. So, if someone got a hold of a user's authentication token and they tried logging in with the token even after the user logged out, they will be able to authenticate into the user's account. 

For a security purpose, it's worth considering invalidating the token once a user logs out, but I won't be handling that for this issue. 

Here's an example call with the authentication token after I logged out

(.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: Bearer <MY TOKEN>"

>> 
HTTP/1.1 200 OK
date: Wed, 29 Jul 2026 05:53:46 GMT
server: uvicorn
content-length: 46
content-type: application/json
x-request-id: 25267264-da6c-4e7b-b564-7c4d0877dd13

{"items":[],"total":0,"page":1,"page_size":20}

However, for this problem I had Claude help me create a token that's expired and tested it and it returns 401 as expected

(.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTgyZTVhOS1jYTFkLTRhMmItYWMwYy03NThkZjBmODBiZDYiLCJleHAiOjE3ODUzMDE5NzJ9.SkDggkNoFfIZrve5J9xcBm4J9noblyITqWRokV_1rPA"
HTTP/1.1 401 Unauthorized
date: Wed, 29 Jul 2026 06:13:31 GMT
server: uvicorn
www-authenticate: Bearer
content-length: 47
content-type: application/json
x-request-id: 9e9e2081-48ea-4d95-90e4-727a3f89f7c4

{"detail":"Invalid authentication credentials"}

Note: I'm sending the request to /reviews endpoint because it's a protected route and required authentication to access. 

Case 2: A request no authorization header 

(.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews                                                               
HTTP/1.1 401 Unauthorized                                                                                                         
date: Wed, 29 Jul 2026 06:15:21 GMT
server: uvicorn
www-authenticate: Bearer
content-length: 30
content-type: application/json
x-request-id: af3aae52-40a4-4a97-8e98-b9b0d7097c4c

{"detail":"Not authenticated"}

### Malformed authorization token:
    Case 3: Bearer with missing token

    (.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: Bearer"                                    
    HTTP/1.1 401 Unauthorized                                                                                                         
    date: Wed, 29 Jul 2026 06:16:39 GMT
    server: uvicorn
    www-authenticate: Bearer
    content-length: 47
    content-type: application/json
    x-request-id: 77765fd0-6506-4029-ad4f-7fde0b0c259f

    {"detail":"Invalid authentication credentials"}

    Case 4: Authorization token with no bearer prefix

    I tested it with a valid token, but without a Bearer, it returns 401 error as expected. 

    (.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTgyZTVhOS1jYTFkLTRhMmItYWMwYy03NThkZjBmODBiZDYiLCJleHAiOjE3ODUzMDY1NjB9.-wVj2-CVo59CulpJm8Y0tIL7O5dvsxobhf3fk9FoQRY"       
    HTTP/1.1 401 Unauthorized
    date: Wed, 29 Jul 2026 06:19:35 GMT
    server: uvicorn
    www-authenticate: Bearer
    content-length: 30
    content-type: application/json
    x-request-id: 9d50d6c4-8232-4e61-a300-51138c97c0c0

    {"detail":"Not authenticated"}

    Case 5: Multiple arguments after Bearer like 'Bearer a b'

    Again, I tested with a valid token, but adding another argument returns an error

    (.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTgyZTVhOS1jYTFkLTRhMmItYWMwYy03NThkZjBmODBiZDYiLCJleHAiOjE3ODUzMDY1NjB9.-wVj2-CVo59CulpJm8Y0tIL7O5dvsxobhf3fk9FoQRY abc123"
    HTTP/1.1 401 Unauthorized
    date: Wed, 29 Jul 2026 06:20:49 GMT
    server: uvicorn
    www-authenticate: Bearer
    content-length: 30
    content-type: application/json
    x-request-id: 6e2be526-92a2-4a79-b2ab-b7002fa257af

    {"detail":"Not authenticated"}

    Case 6: Invalid JWT string (random string or wrong segment count)
    Reproduction: curl.exe -i http://localhost:8000/reviews -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9[]][[[[][][]]]]"

    HTTP/1.1 401 Unauthorized               
    date: Wed, 29 Jul 2026 05:55:59 GMT
    server: uvicorn
    www-authenticate: Bearer
    content-length: 47
    content-type: application/json
    x-request-id: 12b71d92-08c1-4171-afe2-95aeea10f2cb

    {"detail":"Invalid authentication credentials"}
### Case 7: Signed with a different secret than the username and password
    These should throw 401 error

    If an attacker tries to forge a token, assuming they got hold the user email and know the sub, set a future exp, and forges the signature, it would not let the attacker in. 

    (.venv) PS C:\Users\mimi\Documents\GitHub\pathreview> curl.exe -i http://localhost:8000/reviews -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTgyZTVhOS1jYTFkLTRhMmItYWMwYy03NThkZjBmODBiZDYiLCJleHAiOjE3ODUzMDk5MjV9.<forged signature>"
    HTTP/1.1 401 Unauthorized
    date: Wed, 29 Jul 2026 06:46:44 GMT
    server: uvicorn
    www-authenticate: Bearer
    content-length: 47
    content-type: application/json
    x-request-id: 0ebf36ca-0ec8-4232-923b-737dde040d88

    {"detail":"Invalid authentication credentials"}


**PLAN.md link:** [link to PLAN.md in your fork]
https://github.com/mmim14/pathreview/blob/test/90-add-tests-authentication/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

What type of test am I creating? There are 4 subfolders under /tests: bechmarks, integration, security and unit. There are only unit tests. My hunch is the tests for authentication should be under /security. 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

I have added 23 integration test cases for and created 5 files. All of the tasks from PLAN.md are done. 

**Next steps:**
[What are you working on for the rest of the week?]
I will be working on getting my PR draft reviewed by a TF. 

**Blockers:**
[Anything slowing you down? Or leave blank.]
Nothing at the moment. 

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]
https://github.com/ascherj/pathreview/pull/952

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
https://github.com/mmim14/pathreview/tree/test/90-add-tests-authentication

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

Integration tests were missing test for authentication workflow. I added integration tests for the auth middleware, the login/register routes, and the end-to-end auth workflow, verifying authentication behaves as intended and prevents unauthorized access.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

Adds a new integration-test suite (23 in total) under tests/integration/:

- conftest.py — fixtures for a dedicated pathreview_test database and an httpx client wired to the app (overrides get_db so real HTTP requests hit the test DB and not the dev database)
- test_db_connection.py — smoke tests that the DB fixtures work end to end
- test_auth_middleware.py — get_current_user rejects every unauthorized token case with 401: expired, wrong-secret, malformed / bad segment count, missing header, empty Bearer, no-Bearer prefix, and Bearer a b. In addition, it tests a positive control that a valid token is accepted
- test_auth_routes.py ( /auth/register and /auth/login) — token issuance on success, 400 on duplicate email, and a generic 401 on wrong password, unknown email, or inactive user
- test_auth_workflow.py — full workflow: register → log in → use the issued token on a protected route

Screenshot of auth integratiob tests passed:
![integration tests passed](image.png)

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

There was errors that was outside the scope of my issue. My changes didn't affect them.

`make check` before my change:
...
Found 182 errors.
[*] 86 fixable with the --fix option (42 hidden fixes can be enabled with the --unsafe-fixes option).
make: *** [Makefile:51: lint] Error 1


`make check` after my change:
...
Found 182 errors.
[*] 86 fixable with the `--fix` option (42 hidden fixes can be enabled with the `--unsafe-fixes` option).
make: *** [Makefile:51: lint] Error 1

`make test-unit` before my change:
================================== 53 failed, 375 passed, 1 warning in 6.99s ==================================
C:\Users\mimi\Documents\GitHub\pathreview\.venv\Lib\site-packages\_pytest\unraisableexception.py:33: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
  gc.collect()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
make: *** [Makefile:40: test-unit] Error 1

`make test-unit` after my change:
======================================================= 53 failed, 375 passed, 1 warning in 13.03s =======================================================
C:\Users\mimi\Documents\GitHub\pathreview\.venv\Lib\site-packages\_pytest\unraisableexception.py:33: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
  gc.collect()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
make: *** [Makefile:40: test-unit] Error 1

**Draft PR feedback received from:** [name or Slack handle, or "none"]
TF Esha Mehta reviewed my PR. 

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

I didn't expect how long it would take to me to understand the codebase and how 
the authentication workflow is working. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

There are components built that you may not understand it's meaning and why they are set 
the way they are. The file organizations has a reason and it took me time to understand that. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

The AI tool helped tremendously in navigating the codebase and understand
how the components interact. I needed to understand the scope of my work and 
plan it well because AI was suggesting making changes to files that was 
out of my scope of issue. Also, AI did recognize the pattern, but it did not
always follow the pattern that's suitable for the tests I needed to create. 
I had to look at the pre-existing code myself and instruct AI accordingly. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

I think I spent enough time planning and desiging before diving into the code.
I wouldn't change much of the process. I did made mistakes like 
not understanding the role of each of files related to auth. I suppose I could
ask more specific questions to AI to have a clear understanding. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

Understanding the authentication flow at a deeper level and knowing
what the tests are actually doing and being able to explain why my
code does what it does. 