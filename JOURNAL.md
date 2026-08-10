## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/57

**Issue title:** Add a mock GitHub API server for integration tests

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

I can explain what the issue is in my own words as I have done below. I can see the files this code affects and I have read through these as well as what it is testing. I have also located all of the relevant files in the repo after I opened it on Visual Studio. I understand that it looks done when the GitHub tool tests can occur. 

This is my first open source contribution, but I would want to test myself and be able to give myself a challenge. I have looked through this issue in depth and I feel like I am willing to commit time and take this on. I am willing to look through multiple modules to see how everything interacts, so I am choosing a Tier 2 issue. 

I've found and read the specific code the issue references. I've read enough surrounding context that I can write a rough plan for the fix. I admittedly will likely have to look some things up, but I am confident I will be able to understand quickly and figure out what is needed. I have read the test file and know what to contribute. 

I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue. I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline. This issue has no open blockers or dependencies on other unresolved issues. 

**Problem summary:**
The `GitHubTool` in [agent/tools/github_tool.py](agent/tools/github_tool.py) calls the live GitHub REST API (`https://api.github.com`) to fetch repository metadata, so any
integration test that exercises it needs real network access and is subject to GitHub's rate limits and auth. As a result, those tests are skipped in CI, there is currently no
`tests/integration/test_github_tool.py` and no `tests/fixtures/github_responses/` directory, leaving the tool's request handling and error paths (404, 403/rate limit) untested by automation. The fix is to stand up a lightweight local mock HTTP server (`pytest-httpserver`) that serves canned JSON fixtures for GitHub endpoints and to point the tool's `base_url` at it, so the GitHub tool tests can run deterministically and offline in CI without hitting the real API.

**Branch name:** test/57-add-mock-github-api-server

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/TanishaD111/pathreview/commit/31b67ccc409eeeb4ae852756ba168b68e99e02ed

**Reproduction summary:**
Since this issue is to add in a functionality, there is nothing broken because of it. To reproduce it, there is nothing broken to show, but what I do observe is that the two files the review mentions (tests/integration/test_github_tool.py, tests/fixtures/github_responses/) just don't exist yet. Since these tests do not exist and the tool cannot be tested offline since its URL is hardcoded, the two files just arent there. I can see in the agent/tools/github_tool.py file, there is no way to point anything to a url link since the base url is https://api.github.com with no override in the constructor, so its 200/404/403 error paths can only be exercised against the real API, which is why they're skipped in CI. 

**PLAN.md link:** [X] This file is completed

**Blockers or open questions:**
n/a


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All tasks from PLAN.md are done.

**Next steps:**
If I get any feedback on what I have done, I will revisit the issue and make the appropriate changes.

**Blockers:**
n/a

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1021

**Branch:** test/57-add-mock-github-api-server

**What you built:**
This fix was to set up a lightweight mock server that returns fixture responses, enabling GitHub tool tests in CI. Currently, these tests did not exist as there were no GitHub tool tests. I wrote the tests from scratch, which included making the base_url injectable as the hardcoded current URL made the tool untestable. 

**Tests added or updated:**
The test was added in tests/integration.test_github_tool.py. The four fixtures were added in tests/fixtures/github_responses. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
I have received no feedback yet. 

**How you responded:**
I have received no feedback yet. 

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
It was just a new experience working on such a big repository. I am very used to building my own projects and understanding exactly what is going on in a repo. It was a new experience to fix a bug and write tests in someone else's repo. I have contributed to large scale repositories at work, but usually I have more of an idea as to what it is about, so it was definitely surprising to me to be able to do something with many other people fixing other issues within the same codebase. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
With building my own project, I usually kno weverything that imy codebase. I know what all the functions are and what all the files do. It was different to work in someone else's codebase because I had to take time to look through files and folders exploring where everythig was. When I ran the verification checks, I also saw many errors not related to what I was working on. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI tools really helped me understand the code and what I had to work on. I was able to ask Claude to help me while I was creating the planning document. This falls short if I don't understand what the issue was intended to fix. There were times I was recommended to add something to the plan when it was unnecessary. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would change working on the actual fix earlier. I was not able to due to certain family emergencies, but I would have loved to work on the PR earlier next time and being able to get some actual feedback on it before submitting. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
One thing I am most proud of is learning how to make a contribution in an open source codebase. I have always been intimidated of this personally and have never tried, but I am happy to say I have learned the proper way to go about making the fix using AI tools to help as well. Next time if I am working on something like this individually, I know what steps to take in order to create my PR and make my contribution. 