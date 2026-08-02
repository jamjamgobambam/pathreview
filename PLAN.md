## Solution plan

**Issue:** [https://github.com/ascherj/pathreview/issues/70](https://github.com/ascherj/pathreview/issues/70)

### Understand
The rate limiter class is never used or initialized in the API.
When a user tries to access/request too many calls to the API
the rate limiter prevents an excessive number of calls, 
but since the rate limiter class is never used,
users regardless if they are authenticated or not are able
to flood the API with unlimited calls which lead to issues with
server costs and other issues that affect regular users.

### Map
Which files, functions, or modules are involved?
safety\rate_limiter.py
api\middleware

### Plan
1. Connect the rate limiter to the API
2. Initialize the rate limiter when the application starts up
3. Create a limit to control user access

### Inputs & outputs
The fix requires the rate limit to be initialized and take IP address as a
identifier and use a timer and limit number to prevent frequent access.

### Risks & unknowns
What could go wrong? What are you still unsure about?
IP address should remain secure and should be inaccessible to other users and should be deleted once the application is closed.
Using a reasonable rate limit value.
### Edge cases
What inputs or states should your fix handle gracefully?
Null identifier, too frequent rate limiting.