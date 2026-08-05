## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]
- The issue is that there is no test for the `POST /reviews` endpoint when the profile has no ingested documents. Currently, if a user attempts to create a review without any documents ingested, the system may not handle this case properly, potentially leading to errors or unexpected behavior. A successful fix would involve adding a test case that verifies the endpoint's response when there are no ingested documents, ensuring that it returns an appropriate error message or status code.

**Branch name:** test/88-unit-test-review-routes

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Selection Notes:** I chose this tier 1 issue as it is my first open source contribution and I wanted to start with a relatively straightforward task. It involves writing a unit test, which is a good way to get familiar with the codebase and the testing framework used in the project. Additionally, this issue is well-defined and has clear acceptance criteria, making it easier to implement and verify the fix.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** Issue is about creating a test so cannot be reproduced.

**Reproduction summary:**
- None of the existing unit tests go through the http routes testing the APIs listed in the API.md file. They all test internal service functions and modules.
- Basically means there is no structure to follow for testing an API route. I have to figure out how to test the API routes on my own.

**PLAN.md link:** [[link to PLAN.md in your fork]](https://github.com/saineelanjana/pathreview/blob/test/88-unit-test-review-routes/PLAN.md)

**Walkthrough video (recommended):** NA

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I understood how the /reviews endpoint works and how to create a test case for it. 

**Next steps:**
[What are you working on for the rest of the week?]
I will implement the actual test case and run the test suite to ensure that it passes and does not break any existing functionality.

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request] https://github.com/ascherj/pathreview/pull/890

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
test/88-unit-test-review-routes

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I have created a new test case in the `tests/test_reviews.py` file that simulates a request to the `POST /reviews` endpoint with a profile that has no ingested documents. I have verified that the response from the endpoint is as expected, returning an appropriate error message or status code indicating that the operation cannot be completed.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
I created `tests/test_reviews.py`

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
None
