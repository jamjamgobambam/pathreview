## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands
#117
**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands #117

**Tier:** [X] Tier 1 [ ] Tier 2 [ ] Tier 3
**Tier:** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The API documentation explains the available endpoints but does not include example `curl` commands for testing them. This makes it harder for developers who are setting up the project for the first time to verify that the API is running correctly. Adding example `curl` commands will provide an easy way to test each endpoint.
**Branch name:** docs/117-API-docs-issue

**Setup confirmation:** [] App does not run locally at localhost:5173 because of errors and issues which will be dealt with later by
The API documentation explains the available endpoints but does not include example `curl` commands for testing them. This makes it harder for developers who are setting up the project for the first time to verify that the API is running correctly. Adding example `curl` commands will provide an easy way to test each endpoint.
**Branch name:** docs/117-API-docs-issue

**Cohort ledger:** [X] Yes, Issue added to cohort ledger
**Setup confirmation:** [] App does not run locally at localhost:5173 because of errors and issues which will be dealt with later by

**Cohort ledger:** [X] Yes, Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AishaErel/pathreview/commit/57ea620af7605d785e594f2b51c8ad121eb2ddef

**Reproduction summary:**
I started the application locally and successfully tested the POST /auth/register and POST /auth/login endpoints using curl. Although the endpoints work, docs/API.md does not provide example curl commands, requiring new developers to determine the request syntax themselves.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I updated `docs/API.md` by adding example `curl` commands for the documented API endpoints. I manually tested the authentication and profile endpoints locally to verify the request format, had some errors will fix them later.

**Next steps:**

Complete the remaining endpoint examples, review the documentation for consistency, run `make check` and `make test-unit`, open a draft PR, and submit the final pull request.

**Blockers:**

The `POST /profiles` endpoint initially returned a `422` error when uploading a resume PDF. Since the resume upload is optional, I verified the endpoint without a resume and documented the optional upload separately.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/916

**Branch:** `docs/117-API-docs-issue`

**What you built:**

I updated `docs/API.md` by adding example `curl` commands for the authentication, health, profiles, and reviews endpoints. The examples use placeholder values and demonstrate how to authenticate and call protected endpoints using a bearer token.

**Tests added or updated:** I used the tests already being provided

No automated tests were added because this change only updates documentation. I manually verified the documented `curl` commands against the local API where applicable.

**Self-review confirmation:** [ X] make check passes [ X] make test-unit passes (it fails 53 and passes 375, i don't know if 53 fails related with me or if they were already there)

**Draft PR feedback received from:** I opened a PR but nobody responded

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No 

**Summary of feedback:** No reviewer feedback was provided for Summer 2026, as noted in the course instructions.

I requested peer feedback on my draft PR, but I have not received a review yet.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

Testing the API endpoints locally was harder than I expected. I had to make sure the local environment and dependencies were running correctly, understand how authentication worked, and determine the correct request formats for each endpoint. I also ran into issues with the optional PDF resume upload and had to investigate why the profile endpoint was returning errors before confirming that the endpoint worked without a resume.

**What did you learn about working in a large codebase?**

I learned that working in an existing codebase requires understanding the project's existing structure and conventions before making changes. Even though my change was documentation-focused, I still needed to understand how the actual API endpoints worked so that the `curl` examples were accurate. I also learned the importance of working on the correct branch, keeping commits organized, resolving Git conflicts, and testing changes before opening a pull request.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar Git commands, troubleshoot errors, interpret API responses, and create and test `curl` commands. They were also useful for helping me understand the workflow for authentication and protected API endpoints. 

**What would you do differently if you started over?**

I would review the API documentation, contribution guidelines, and endpoint requirements earlier before starting the implementation. I would also make sure my local branch was synchronized with the remote branch before making changes. 
**What are you most proud of from this module?**

I am most proud of becoming more comfortable working through the full contribution process in an existing codebase. I was able to reproduce the documentation gap, create a plan, test the API locally, add practical `curl` examples, work through Git and authentication issues, and open a pull request with my changes.

