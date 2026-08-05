## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/13]

**Issue title:** [Add a content hash to detect unchanged documents and skip re-embedding]

**Tier:** [Tier 2] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]
The issue is that when a user re-submits the same README file without making any chnages the whole file still gets re-embbeded, leading to more unnessary API calls. A fix for this issue would be to create a hash of the README and only re-embed the file if the hash changes at all. To implement this fix, a hash for the readme will need to be processed at every upload and stored for future uploads. This will primarily effect the ingestion pipline

**Branch name:** [feat/13-add-conditional-hash-re-embedding]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

This issue is right for me!

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/ascherj/pathreview/commit/f4a227031894ad27db4b16200dafcc97cb07efab]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced my issue using unit tests. Since, this is a feature I cannot directly reproduce this issue. I instead created unit tests to help reproduce the intended behavior beind this issue (IE: skipping readme if already ingested identical copy).

**PLAN.md link:** [https://github.com/mtemkin31415/pathreview/blob/feat/13-add-conditional-hash-re-embedding/PLAN.md]

**Walkthrough video (recommended):** [None present]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
No blockers here :)


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have currently implemented the solution for issue #13 and have implemented a conditional check to see if the readme has already been uploaded to a users' repo by using a content based hash. I just commited all the test cases for the project as well. 

**Next steps:**
The next step is to properly verify that my change is ready to be submitted for a pr. Running all unit tests again and making sure my changes didn't affect any other code. Then I will open and write a pull request draft.

**Blockers:**
I little unfamilliar with creating test cases in Python but using AI and other test files to help me.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/425]

**Branch:** [feat/13-add-conditional-hash-re-embedding]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I added a conditional check to the readme parser that skips README ingestion if the contents of the README hasn't changed between uploads. I added functionality to the check_skip function where the db query returns whether a simmilar file exists and also the _add_ingestedResource function which adds the ingested readme to the database.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
Added file: tests/unit/test_ingestion_pipeline.py. The tests cover the scenarios where two identical readmes are uploaded to the ingestion pipeline one after another. There are scenarios that check for the exisitng functionality as well. I also covered the edge cases where an identical readme is passed to another repository.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in (As to be expected)

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
I felt it was tough navigating the codebase and getting used to the way the workflow was set up. Especially since so much of the codebase wasn't implemented yet, it was difficult to see how the ingestion process worked/how it was supposed to work. I felt like I also had to make a good amount of personal design descisions which was cool, because I'm not used to being in charge of the codebase architecture.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I definitely realize how important comments are when working on a foregin codebase. Since there is no documentation of architecture, design descions, ingestion processes or database flows, it's really important to rely on good variable/method naming and solid function definitions to make my way around the codebase. When you build a codebase from scratch, it is easier to know what every line of code does, but I also think it makes it easier to make bad/confusing designs that will make it hard for any other developers working on the same project.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI assistance was not as useful here as in the other modules. I think the scale of this module was way smaller than in the other modules and the changes that I needed to make were pretty easy to see. I  AI was most useful here for writing the necessary DB queries and writing the unit test cases. I think writing unit tests is especially boring to do, so I really liked that the AI was able to think of many test cases, even edge cases, and to implement them with ease. I thought it was easier to implement the specific changes for my issue myself. When the AI touched the codebase it changed way more than what was needed, due to the unfinished nature of the codebase, so I found it easier to just make the changes myself.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I think I might try a slightly more difficult issue. Once I completed the planning phase, I was basically ready to submit my PR afterwards because I knew exactly what code I needed to write.  I think a harder issue may have been more interesting and required more time and planning from me. I really liked how I planned the implementation, so I knew exactly what changes I needed to make for week 9. I also shoud've held off on creating the test cases for a little longer until I fully grasped what needed to be changed.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I think I am most proud of how quickly I was able to understand the codebase. Once, I started looking at the ingestion_pipeline and the models I felt like the structure really clicked for me and had a decent understanding of what to expect before I started running the app. I work with a large codebase as part of my job, so it's nice to see my skills visibly improving like this.