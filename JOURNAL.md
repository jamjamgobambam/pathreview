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

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** NA

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]