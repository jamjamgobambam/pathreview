# Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user #43
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]
When a user submits a review, the agent reviews their submission, generates the result of the review tools, and caches the agent state. However, if a user updates their portfolio and requests a second review, the agent reuses the same results rather than compute a new one. This means that rather than review the newly updated portfolio, the user gets feedback on their previous submission.

**Branch name:** fix/43-agent-state-not-cleared

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## "Is this right for me?" Checklist

## Part 1 — Understanding the issue
### Can I explain what this issue is asking for in my own words?
Yes, I believe my 3-5 sentences were suffice enough to explain to anyone about what the problem is, and give them a picture of what should be solved.

### Do I understand which part of the app is affected?
labels: "agent"
relevant files: "agent/memory/session_store.py"

These were given in the issue tab, and gives a general overview on what files I should check and understand before making any changes. 

### Do I understand what "done" looks like?

Currently, when the user submits a review and gets feedback on it, the session is saved. However, when the user submits a second review, the agent reuses the same feedback from the first review.

For this issue to be considered "resolved", the agent must be able to reset their session for each independent review under the same user. What this means is that for the first review, the agent creates a session state with its responses. For the second review, the agent must be able to clear the previous session state and generate a new response for the updated review.

## Part 2 — Tier Fit
Because this is my first open source contribution, I'm choosing Tier 1 to learn the basics and understand the whole workflow before moving on.

## Part 3 — Codebase Readiness
### Can I find the relevant code?
The relevant files given was "agent/memory/session_store.py". Given here, I retraced the code to see what files called this function, and found "orchestrator.py" utilized ".get" and '.update". I utilized Claude to help me find where these function methods were used.
### Do I understand the surrounding code well enough to change it safely?
Having traced the relevant files to where it is used throughout the project, I believe I understand the surrounding code well enough to make sure that any changes made only impact the files that used the function.

### Have I read the relevant test file?
I took a look at "tests/unit/", but were unable to find a test file for my issue. I'll most likely produce a test file using Claude as I proceed with the isuse to make sure that my changes fixed the issue or not.

## Part 4 — Scope and Time
### How many others are already working on this issue?
There are 23 listed on the ledger, making me the 24th. Since it's my first open source contribution, I'm fine with this count.
### Is the scope realistic for Weeks 8–9?
Since its Tier 1, I believe it's feasible to complete before Week 9.
### Are there any blockers or dependencies?
No open blockers or dependencies.

# Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AI201-Applications-of-AI-Engineering/pathreview/commit/08fd74e1ec17692fc04d7f115b6d44ed3b3435e8

**Reproduction summary:**
<!-- [1–2 sentences: How did you reproduce the issue? What did you observe?] -->
I utilized Claude to help regenerate the issue. I based my PLAN.md and JOURNAL.md, and asked it to reproduce what the issue can occur. Afterwards, I asked it to store it in a file, in which it is now located in "/tests/unit/test_orchestrator_session_reset.py".

**PLAN.md link:** https://github.com/AI201-Applications-of-AI-Engineering/pathreview/blob/fix/43-agent-state-not-cleared/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

# Week 9 — Solution building & PR submission

## Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I've completed the fix, having tested with the sample test file that I've built. To make sure there were no issues, I ran the file before and after my change to make sure there were noticeable changes. 

**Next steps:**
[What are you working on for the rest of the week?]
Addressing the PR, seeing if I can improve on it, and if I am missing anything, and practice more of it.
**Blockers:**
[Anything slowing you down? Or leave blank.]
I am submitting this a week later than the actual due date, so I apologize if I'm not able to get feedback for myself. Thank you for all the help this year.
---

## Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1008

**Branch:** 
<!-- [the branch name you worked on, e.g. `fix/123-short-description`] -->
fix/43-agent-state-not-cleared 

**What you built:**
The original bug was that when a user requests a review, they are able to receive feedback on it. However, if the user submits a revised review, the stored session still contained the results from the first review instead of producing a clean fresh analysis of the new submission. What I've done is completely remove the loading of the previous state, which caused a buggy merge, and directly store the results of the new review within the state by overwriting what was previously there. 

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
Because there was no test file made for this bug, I created a sample test file, named "test_orchestrator_session_reset.py". This test file tested the leak existed before the fix, and what it outputted after the fix by having one user submitting two reviews against a shared store. The test would fail if the orchestrator merged review 2 onto review 1's state, and would pass if it replaced the state. 

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
NOTE: The errors that existed before the change and after the change remained, but the changes introduced zero new failures. Because this error did not have its own test as part of the test-unit, I had to manually add the test into it to make sure that it passed.

**Draft PR feedback received from:** [name or Slack handle, or "none"]

# Week 10 — Iteration & reflection

## Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No reviews yet.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

## Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
Having this as my first PR ever, understanding the process and successfully following the guidelines was probably the hardest part for me. Because I was new to this process, I didn't know where to start or where to look at. Though I was able to use AI to try to understand the project that I was working with, I still didn't know exactly where to start. Because of this, having AI actually saved so much time, directing me to where the bug occurred. Having figured this out, the next step was understanding what the code did, and backtracking from here to figure out where it starts and then process it up. Once I was able to understand (and having Claude to help me out with examples and clarifications), I was able to find the issue by isolating predicted/actual results and having Claude help me print the actual errors, and go from there.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
Working in a large codebase gave me an experience on how other SWEs work. Not everything is start from scratch; many times, it starts with an older production base, and it's with this project that I learned the fundamentals of SWE. Having to first understand the problem, understanding the codebase, and then connecting the two to find the issue. While this is my simplified version of what SWEs do, I felt like this was a very good step to understanding how to contribute to future bigger projects, and I'll be able to learn more as I go.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI assistance was best for me in understanding where to start, what the files that were associated with the issues did, and where the problem occurred. Having the baseline of the problems, I was able to study each file and understand what they did, vs what they are suppose to do. 
Though I had AI to help me understand and isolate the bug, I didn't use it to write my statements. I wanted the readers to understand what I wrote, and understand clearly so that when future reviewers read this issue, they are able to understand what I wanted to do, and what the expected results were. Because AI writes very robotic, I figure writing everything myself could allow reviewers to know that every statement was written to be understood at layman's terms.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
Doing everything in one go. Starting from the issue selection to planning to implementation, I want to be able to understand everything in the beginning before trying to figure out where the error occurred.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
Being able to know what to do from start to finish. Even if there was one thing wrong or something that I could've done better, this was a learning experience for me and any sort of success/failure helps me grow.