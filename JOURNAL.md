## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/80]

**Issue title:** [DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings #80]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
[When a user is deleted their associated reviews and vector store embeddings are left in the app. A successful bug fix would delete the reviews associated with the deleted user from the postgreSQL database and the user's associated vector store embeddings. This would involve mostly working with the api and databases]

**Branch name:** [fix/80-cascading-delete]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]
https://github.com/CrabHeadd/pathreview/commit/a3e3abfa573c60db6442778b01f70b6889900e63
**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
When I deleted user1@example.com by authenticating on the swagger ui and then inputting their profile id, all of their reviews were deleted in the docker database as expected, I checked, however in the /profiles/{profile_id} delete endpoint, and in the function delete_profile in profile_service.py called by the endpoint, nothing ever gets rid of the vector store embeddings associated with the deleted user, thus they are likely still there. 

**PLAN.md link:** [link to PLAN.md in your fork]
https://github.com/CrabHeadd/pathreview/commit/a3e3abfa573c60db6442778b01f70b6889900e63#diff-1d972b4ac04c89bf54f79f2111064626b16aeb8bb9488f4ca0aed3ab1e728d2c
**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
There was supposed to be orphaned reviews? But I checked inside the database and the reviews that had their profile deleted were deleted. Also am a little unsure of how to work with the vector store embeddings, but the function delete_by_source_id in profile_service.py gives me hope.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I found out how to view the vector store embeddings and read more of the code.

**Next steps:**
[What are you working on for the rest of the week?]
Will work on trying to find out how to utilize already implemented functions to get rid of vector store embeddings

**Blockers:**
[Anything slowing you down? Or leave blank.]
Code is very confusing, lots of classes are not used execpt by larger classes and those are hardly used except for maybe a few tests, I don't even know if the whole thing really works? Code seems very poorly held together
---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]
https://github.com/ascherj/pathreview/pull/957

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
fix/80-cascading-delete
**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
added some code to core/services/profile_service.py function delete_profile to delete orphaned vector store embeddings
**Tests added or updated:**
[Which test files did you touch? What do they cover?]
core/services/profile_service.py
**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review
**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

Working with an incomplete source code was the most difficult part of the project, as it meant that I wasn't too sure how things fit together, and how to implement my own fixes. It felt more like I was coding based off of gut feeling rather than what I knew for certain

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

Sometimes it might not be very put together, which makes it more hard to navigate. Also I did not realize testing was such a large part of this.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

After trying to navigate the codebase myself for a while I then opted to try and let ChatGPT give it a go and tried to explain the whole project and gave it snippets of code, but it even confessed that it was unsure of how the whole thing worked. Thus it didn't really help. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

I would choose an easier issue, as I thought that the tier 2 problem sounded easy, but working with the large codebase made it significantly harder

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

I am most proud of actually trying to get everything working, despite not really understanding much of it. Before I started this course I didn't even know you could do half of this stuff in python, like accessing databases and making a whole ui.