## Week 7 — Issue selection

**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/86)
**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently there is no rate limiting implemented on the API endpoint, the only limiter is the mocked Redis one that shows why the unit test passed rather than the live program. When I, the user tried to make many requests they were all 200 ok which shows why I was not able to get 429. I will need to add the middle ware of the rate limiting along with the headers to notify the users how many requests. Since its a middle ware, I dont need to go implement it for all routes as all responses will need to go through my middle ware.

**Branch name:** `fix/86-api-rate-limiting-header`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### **Selection Notes:**

**Do I understand which part of the app is affected?**

Yes. This touches `api/middleware/` (currently only `request_id.py` and an 
auth middleware exist — no rate limiting middleware), `safety/rate_limiter.py` 
(the unused `RateLimiter` class), and `core/config.py` (unused 
`rate_limit_per_minute` setting). I confirmed all three files exist and read 
their contents directly.

**Do I understand what "done" looks like?**

Yes. Before: authenticated requests to any endpoint always return 200, no 
matter how many are sent in a short window, and no response includes rate 
limit information. After: once a client exceeds [X] requests in [window], 
they receive a 429 response; every response (whether allowed or blocked) 
includes `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers so clients 
can proactively back off before hitting the limit.

**Can I find the relevant code?**

Yes. I read `RateLimiter.check_rate_limit()` in full, including its Redis 
sorted-set logic and fail-open behavior on Redis errors. I also read 
`RequestIDMiddleware` in `api/middleware/request_id.py` as the structural 
template for how middleware is written and registered in this app, and 
traced `main.py` to see exactly where and how `add_middleware()` calls are 
wired in.

**Scope:**

I have worked with other large codebases before like Thonny and Idle Python Editors, so I believe this issue will be addressed within the next couple of weeks.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I went to `http://localhost:8000/docs#/reviews/list_reviews_endpoint_reviews_get` and logged in with `user1.example.com` on the lock icon to generate a curl command of the reviews. Then I used the terminal with the following commands. Where the key is the token generated with the curl command.
``` bash
TOKEN=<Key>

for i in {1..1000}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8000/reviews?page=1&page_size=20" \
    -H "Authorization: Bearer $TOKEN")
  echo "$code"
done > status_code.log
```
Once it's done running, I ran `sort status_code.log | uniq -c` and it showed `1000 200` in the terminal.

These commands prints the status codes of 1000 GET requests made for the reviews page and prints it out to a `status_code.log` file then the `sort status_code.log | uniq -c` finds different instances of status codes. `1000 200` means that there are 1000 instances of 200 status codes and shows no 429 meaning a rate limiter has not been implemented for the API. I also ran the test suite for `tests/unit/test_rate_limiter.py`, it shows that all tests passed, but upon further inspection, it only tests on a mocked Redis rather than actual requests from the API.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]