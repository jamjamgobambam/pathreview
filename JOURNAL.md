## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/89)

**Issue title:** API reference doc is missing the POST /profiles request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [] Tier 3

**Problem summary:**

The issue lies within docs/API.md. The doc currently documents response schemas for endpoints, but is missing request body schemas for the POST /profiles and POST /reviews endpoints. Without these, someone integrating against the API has to guess at what fields to send. To remedy this, we need to add request body schemas for both endpoints, each with field descriptions and example values.

**Branch name:** fix/89-API-reference-doc-missing-POST-profiles-schema

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Issue Checklist

**Can I explain what this issue is asking for in my own words?**

Yes. The API currently is missing schemas for POST /profiles endpoint.

**Do I understand which part of the app is affected?**

Yes. The API.md doc is the root cause of the problem, and also the affected portion.

**Do I understand what "done" looks like?**

'done' means that the doc is updated with schemas and examples, following the format of other schemas in the doc.

**Is the tier a realistic match for where I am right now?**

While the fix seems pretty simple, this is my first time working with a large codebase or open source project, so it is a good fit for me.

**Can I find the relevant code?**

Yes, the relevant portion of this issue is, as mentioned, the API.md file, which has descriptions for other endpoints, but not the one described here.

**Do I understand the surrounding code well enough to change it safely?**

I understand how the other API endpoints are structured, so I do undesrstand how to best document this one.

**Have I read the relevant test file?**

Since this is a docs issue, there isn't really any test files for this.

**How many others are already working on this issue?**

There are large amount of people working on this issue, but since it is a documentation gap, I am ok with the amount of people working on it.

**Is the scope realistic for Weeks 8–9?**

Yes. All I need to do is understand the API structure and document it.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to comment commit](https://github.com/dRamachandran7/pathreview/commit/2edeee5972e5cf60b9769c7448321dc74e57d057)

**Reproduction summary:**
Upon inspecting the schemas, we can see that the two endpoints described do indeed exist, and upon inspecting API.md, we can see that they are not documented. This is the gap we need to fill.

**PLAN.md link:** https://github.com/dRamachandran7/pathreview/blob/fix/89-API-reference-doc-missing-POST-profiles-schema/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

So far, I've gone through schemas/profile.py, and understood the structure of the response json, and the constraints on each of the parameters

**Next steps:**

For the rest of the week, I'll be documenting the actual response structure, along with coming up with good examples to provide for the response.

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/579

**Branch:**  fix/89-API-reference-doc-missing-POST-profiles-schema

**What you built:**

I added documentation for the POST /profiles API endpoint. I explained each parameter, and provided examples.

**Tests added or updated:**

No test files were added or updated since this is a documentation change, but no new failures were introduced.

Before and after my changes, 53 tests failed and 375 passed.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**

The reviewer mentioned a couple things:

- Considering changing the PR title to something more descriptive, mentioning the change and issue reference
- Give more info on the changes made in the PR description so a reviewer does not have to check the diff. 
- My commit messages didn't exactly follow the guidelines, so I could have rebased to fix that.

**How you responded:**

I updated the PR title, making it more descriptive as mentioned, changing it to 'Document POST /profiles response schema (#89)'. I also updated my PR description to say exactly what file was changed and how it was changed.

---

### Reflection

**What was harder than you expected?**

Understanding the app structure, and knowing where to look to find the api endpoint and schema took some time. It took more time to then formulate an example that was accurate and represented the app properly.

**What did you learn about working in a large codebase?**

I learned about following the contributing rules closely, making sure to follow the structure of the codebase. I recieved feedback relating to my adherence to these rules, such as the feedback on the commit messages.

**How did AI tools help — and where did they fall short?**

AI did help me get a good place to start, summarizing the app structure and telling me where to find the schemas. It also helped me understand how they were used. However, when it comes to documentation, I found it useful to write it myself to make sure it made sense. 

**What would you do differently if you started over?**

I would've picked a larger issue. This issue was actually about 20 lines of documentation, and I wish I had picked something more interesting to work on.

**What are you most proud of from this module?**

I'm proud that I was able to navigate a large codebase and successfuly add something to it.
