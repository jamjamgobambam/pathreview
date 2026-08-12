## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands
 

**Tier:** [ O ] Tier 1  [  ] Tier 2  [  ] Tier 3

**Problem summary:**
[the api.md file contains information about the endpoints but there is no mention of examples to call it. This issue causes users to be unable to easily test that the api is working as intended. After I fix the issue the documentation should have the updated curl commands so that users can validate the api easily.]

**Branch name:** [docs/117-add-example-curl]

**Setup confirmation:** [ O ] App runs locally at localhost:5173

**Cohort ledger:** [ O ] Issue added to cohort ledger

## Reproducing issue Locally
After reading the api.md file in the docs file, I confirmed that the issue persisted as there is no examples of any curl commands.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/M0hayan/pathreview/commit/d95b4aae625c89353e658bca3fb8526dd8915f03]

**Reproduction summary:**
[I had to clone the repo locally and take the steps so that the app was working as intended. Then I read through the documentation and confirmed that there are no example curl commands in the api.md file.]

**PLAN.md link:** [https://github.com/M0hayan/pathreview/blob/docs/117-add-example-curl/PLAN.md]

**Walkthrough video (recommended):** []

**Blockers or open questions:**
[]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Updated `docs/API.md` to include example `curl` commands for the documented API endpoints. Reviewed the FastAPI route implementations to verify the correct request formats, authentication requirements, and endpoint behavior.

Completed sub-tasks:
- Reviewed existing API documentation and identified missing invocation examples.
- Verified endpoint methods, paths, and request formats against the API implementation.
- Added examples for Health, Authentication, Profiles, and Reviews endpoints.
- Documented required placeholders such as `<token>`, `<profile_id>`, and `<review_id>`.

**Next steps:**
- Review the updated documentation for formatting and accuracy.
- Run any required project checks before opening the PR.
- Submit the pull request and address any reviewer feedback.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** [(https://github.com/ascherj/pathreview/pull/931)]

**Branch:** `docs/117-api-example-invocations`

**What you built:**
Updated `docs/API.md` with runnable `curl` examples for the API endpoints so new developers can quickly verify the service is working. The examples were aligned with the actual FastAPI implementation, including OAuth2 form-based login, multipart profile creation, and authenticated requests using bearer tokens.

**Tests added or updated:**
None. This was a documentation-only change, so no application behavior was modified and no unit tests were required.

**Self-review confirmation:**  
[ O ] make check passes  
[ O ] make test-unit passes  

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ O ] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
N/A No feedback for summer term

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
N/A No feedback for summer term
---

### Reflection

**What was harder than you expected?**
[The part that was harder than I expected was making sure the curl examples actually matched how the API worked. At first, the issue seemed like it would just require adding a few example commands to API.md, but I had to look through the FastAPI route implementations to confirm the correct methods, paths, request formats, authentication requirements, and parameters. For example, the login endpoint uses OAuth2 form data, while profile creation uses multipart form data. This meant I could not just write generic curl examples based on the endpoint names.]

**What did you learn about working in a large codebase?**
[I learned that working in someone else's codebase requires more investigation than working on a project from scratch. I already knew what I wanted to change, but I had to understand how the existing API was implemented before making the documentation change. Small changes can depend on details in other parts of the project, so it is important to search through the code and verify assumptions instead of just making the change based on the issue description.]

**How did AI tools help — and where did they fall short?**
[AI tools were most useful for helping me understand the existing code and documentation and for thinking through what information should be included in the API examples. They helped me work through the structure of the documentation and identify details I needed to verify. However, I still needed to inspect the actual FastAPI routes myself. AI could suggest what a curl command might look like, but I needed to confirm that the commands matched the implementation instead of assuming the suggestions were correct.]

**What would you do differently if you started over?**
[If I started over, I would spend more time looking through the API implementation before planning the documentation changes. I initially thought the issue would be very simple because it was a documentation issue, but understanding the different request formats and authentication requirements took more investigation than expected. I would also make the plan more detailed from the beginning about which endpoints needed examples and what information each example needed to demonstrate.]

**What are you most proud of from this module?**
[I am most proud of being able to make a useful contribution to an existing project without changing any application code. The final documentation gives developers concrete curl commands they can use to test the API instead of only describing the endpoints. I also made sure the examples were based on the actual FastAPI implementation, which made the change more than just adding examples that looked correct.]
