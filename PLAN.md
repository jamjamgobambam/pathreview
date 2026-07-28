## Solution plan

**Issue:** [Add an API rate limiting header (X-RateLimit-Remaining) to responses #86](https://github.com/ascherj/pathreview/issues/86)

### Understand
safety/rate_limiter.py calculates the count of requests left until the limit is reached and correctly returns True or False along with the remaining count of requests. However, no middleware exists to throw an error or include headers containing the request count information. The expected behavior is that the "True" case will return the response to the user and a header containing the requests remaining and limit (X-RateLimit-Limit and X-RateLimit-Remaining). The "False" case will throw a 429 error stating that the request limit has been exceeded. These responses will be coded in a new file in api/middleware.

### Map
The files involved are safety/rate_limiter.py, specifically the check_rate_limit function, api/middleware/auth.py, api/middleware/request_id.py, and api/main.py. I expect to create a new file called rate_limit.py in api/middleware. This file will follow the structure of the dispatch method in request_id.py to call the check_rate_limit function and then follow the structure of get_current_user in auth.py to decide whether to throw an error or return a response. I will create an integration test file to assert that my change works as intended.

### Plan
    1. Create api/middleware/rate_limit.py
    2. Register headers in api/main.py
    3. Add tests/integration/test_rate_limit_header.py file to ensure that response is returned correctly with headers.

### Inputs & outputs
My fix takes the same things as input request identifier, limit, and window_seconds. The output should change as each response should include X-RateLimit-Limit and X-RateLimit-Remaining headers. In the case of the user exceeding the limit, a 429 HTTPException should be thrown.

### Risks & unknowns
The exception may not be caught correctly or the headers may not be registered with the expected format.

### Edge cases
The fix should handle the case of a user exceeding the limit request by throwing a 429 error. The input is predefined and should not be changed by this fix.