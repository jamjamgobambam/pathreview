## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example curl commands
 #117

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API documentation is missing example calls to the API endpoints. This lack
of documentation makes it difficult for developers to quickly test whether the
API is working. Adding example `curl` commands to `docs/API.md` would fix
this by giving developers something they can copy, run, and get a real
response from.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/casuallama/pathreview/commit/a2bec6874f3386d7827f7981b14838c5743334aa

**Reproduction summary:**
Reviewed `docs/API.md` and confirmed every listed endpoint (health, auth, profiles, reviews) is documented only as a method + path + one-line description, with no accompanying `curl` request or example response anywhere in the file — matching the gap described in issue #117 exactly. The fix is to add a runnable `curl` example (and expected response) under each endpoint.

**PLAN.md link:** https://github.com/casuallama/pathreview/blob/docs/117-api-curl-examples/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Should I also document PUT /profiles/{profile_id} and GET /reviews/{review_id}/status?

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have not implemented anything. Still getting around to working on this project.

**Next steps:**
Setting up environment well, I did not do that last assignment because it was a documentation issue so I didn't see the need to. And then implementing my changes to the API docs.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/793

**Branch:** docs/17-api-curl-examples

**What you built:**
I added the curl examples to the API documentation.

**Tests added or updated:**
Did not touch any test files.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The setup for this project was more difficult than I expected, especially the docker setup. I ended up having to go into my BIOS and enabling virtualization because it wasn't on by default. I was also tripped up with switching between Git Bash and Powershell as well, so commands I expected to work did not and I spent time debugging when it was just a matter of switching.

**What did you learn about working in a large codebase?**
Getting familiar with the codebase is always a step you must take when working with a project like this. With my own projects, I'm usually familiar with every file and function and my personal projects are usually simpler. With this project, I learned that documentation was extremely helpful when working in a large codebase, as it provides you with concrete information and a good place to start.

**How did AI tools help — and where did they fall short?**
AI assistant was the most helpful when summarizing the file structure and overall functionality of the project and its modules. Where it fell short was helping me test certain outputs with curl commands. This was expected though, because I needed to do this on my own terminal and with my local variables.

**What would you do differently if you started over?**
I think I would have chosen a different issue. Although it was interesting contributing to the actual documentation for a real project, I wish that I had chosen an issue that had some coding. It would have been a nice experience to have hands on practice with an open source project.

**What are you most proud of from this module?**
I am proud of learning how the PR process works and the conventions around it. I think that it is very important for people who don't have professional experience with Github. Now that I've practiced this I can even find and contribute to other open source projects or bring that experience to the workplace.