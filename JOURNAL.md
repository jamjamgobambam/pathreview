# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API documentation explains each endpoint but does not include example `curl` commands that developers can use to test the API. This makes it harder for new contributors to verify their local setup and understand how each endpoint should be called. I updated the documentation by adding example `curl` commands for the documented endpoints so developers can test the API more easily.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Is this right for me?

- [x] The scope appears manageable within the course timeline.
- [x] I understand the area of the codebase involved.
- [x] The issue provides a good opportunity to learn more about the project.
- [x] I have a plan to reproduce the issue, implement a fix, and test my changes.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DarrenBoyo/pathreview/commit/40e5704

**Reproduction summary:**
I reproduced Issue #117 by reviewing `docs/API.md` and confirming that the API endpoints were documented without example `curl` commands. Developers had to rely on the backend implementation or Swagger UI to determine how to call and test the endpoints.

**PLAN.md link:** https://github.com/DarrenBoyo/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I needed to verify which endpoints required authentication and ensure the `curl` examples matched the current API implementation.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reviewed the API route implementations and confirmed how each endpoint is used. I updated `docs/API.md` by adding example `curl` commands for the Health, Authentication, Profiles, and Reviews endpoints. The examples include the correct HTTP methods, authentication requirements, and request formats based on the current implementation.

**Next steps:**
Run the project verification commands, request peer feedback on my pull request, make any necessary revisions, and submit the completed PR.

**Blockers:**
I initially could not run the project's Makefile because GNU Make and the local development environment were not configured on Windows. After installing GNU Make, configuring Docker, and completing the project setup, I was able to run the project's verification commands.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/248

**Branch:** `docs/117-api-curl-examples`

**What you built:**
I updated the API documentation by adding example `curl` commands for all documented endpoints. The new examples demonstrate how to authenticate, send requests, and access protected endpoints using bearer tokens, making the documentation easier for contributors to understand and test.

**Tests added or updated:**
No test files were modified because this contribution only updates project documentation. I verified the `curl` examples against the API route implementations. I also ran the project's verification commands. `make check` reported existing repository-wide lint issues unrelated to my documentation changes, and `make test-unit` completed with 375 passing tests and 53 existing failures in unrelated project modules.

**Self-review confirmation:**
- [ ] make check passes
- [ ] make test-unit passes

**Draft PR feedback received from:**
None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
The reviewer said that the `curl` examples described in my journal did not appear to be present for the Authentication, Profiles, and Reviews sections. They recommended doing a final review of the actual PR diff to make sure the completed work matches what is described in my journal and plan. I also received feedback about my testing documentation because I did not clearly distinguish between pre-existing test and lint failures and the results after my changes. The reviewer also recommended requesting peer feedback earlier in the contribution process.

**How you responded:**
I reviewed the current version of `docs/API.md` and confirmed that it contains `curl` examples for the Health, Authentication, Profiles, and Reviews endpoints. I also reviewed my testing documentation to make sure it accurately explains the existing lint and unit-test failures that are unrelated to my documentation changes. The feedback helped me understand the importance of checking the final PR diff before submitting my work.

---

### Reflection

**What was harder than you expected?**
Setting up the development environment was harder than I expected. I ran into problems with Docker, GNU Make, Git Bash, and the Python virtual environment on Windows. I also had to become more comfortable working with forks, branches, commits, and pull requests. Even though my issue focused on documentation, completing the contribution required understanding and using the project's full development workflow.

**What did you learn about working in a large codebase?**
I learned that I cannot rely only on the issue description when making a change. I had to inspect the API route implementations to understand authentication requirements, request formats, parameters, and how the endpoints actually work before writing the `curl` examples. I also learned that a large repository can already contain failing tests and lint errors. It is important to establish which problems existed before making changes so I can determine whether my contribution introduced any new failures.

**How did AI tools help — and where did they fall short?**
AI tools helped me understand Git commands, troubleshoot Docker and Make errors, navigate unfamiliar parts of the codebase, and understand what different error messages meant. AI was also useful for helping me organize my plan and documentation. However, I learned that AI suggestions still need to be checked against the actual repository. I needed to inspect the route implementations, GitHub diff, and test results myself because the codebase is the final source of truth.

**What would you do differently if you started over?**
I would set up my complete development environment before beginning the issue and run `make check` and `make test-unit` before making any changes. This would give me a clear baseline that I could compare against my results after implementing the fix. I would also review my final PR diff more carefully and request peer feedback earlier so that potential issues could be identified before submission.

**What are you most proud of from this module?**
I am most proud of becoming more comfortable with the complete open-source contribution workflow. I learned how to work with a fork, create and manage a branch, investigate an issue, plan a solution, make and push changes, run project verification commands, and maintain a pull request. I now have a much better understanding of what it takes to contribute to an existing project rather than only working on my own code.