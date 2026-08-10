## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/71

**Issue title:** Implement a red-teaming test suite for the prompt injection defense #71

**Tier:** [ ] Tier 1  [ ] Tier 2  [*] Tier 3

**Selection Notes:**

Currently my degree and focus is cybersecurity and computer science. This issue does seem difficult in relation to the size of the overall project but relatable to projects I have done during my senior year and in topic. These projects include making a vulnerability prediction tool using linear regression and other models to predict the impact the vulnerabilities on a csv of windows exploits. This issue is actually defending against a vulnerability like prompt injection which requires generating tests and searching examples used by malicious actors. Research and understanding the layout of this project are strong skills used by cybersecurity individuals every day.


**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue consists of creating security test automations that run every time a pull request is made to safely catch changes that weaken the safety layer. These test focus on the safety layer and defending against prompt injection through the ingestion of resumes. These tests affect every file that touches the safety layer and runs in the command line automatically. Currently this app includes no automatic test during pull requests that touch the safety layer. The goal is to protect against various different prompt injection techniques and running tests automatically during PRs to keep that security stable.

**Branch name:** https://github.com/Dannypxp/pathreview/tree/feat/71-red-teaming-suite

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger




## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/1d83a53eeb9263a07db006c947146898354e3a6a

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

To reproduce the issue, I had to go into "tests/security" to see the red-team suite was not created and no test file was found, this means I would have to create the suite from scratch.

**PLAN.md link:** https://github.com/Dannypxp/pathreview/blob/feat/71-red-teaming-suite/PLAN.md

**Walkthrough video (recommended):** (https://www.loom.com/share/df5fa1c88f0a4eb08ecea3ca12424c9a)

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
So far I have completed three sub tasks which were to research the missing prompt injection tests from prompt_defense.py, created the new prompt_injection payloads and the test_prompt_injection.py to run the payloads.

**Next steps:**
[What are you working on for the rest of the week?]
Next steps are to wire the red team suite to the ci to run the tests every time a pr touches "safety/". Furthermore, I still have to create conditions for the two edge cases which are for submitting a pr that did not touch "safety/" and for when a pr changes/alters the prompt_injection tests. Lastly I have to make my pr to submit the assignment.
**Blockers:**
[Anything slowing you down? Or leave blank.]
Claude was down around 4pm on Wednesday, it halted my work 
---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/465

**Branch:** 

feat/71-red-teaming-suite

**What you built:**

Built a red-team test suite for the prompt injection defense: added `tests/security/test_prompt_injection.py`, a fixture corpus of 13 curated attack payloads in `tests/fixtures/injection_attempts/`, and a `test-security` job in `ci.yml` that runs the suite when a PR touches `safety/`, skips when it doesn't, and fails if the fixtures or tests are weakened or deleted.

**Tests added or updated:**

Added `tests/security/test_prompt_injection.py`, covering 6 categories of known prompt injection attacks: role-switching (`System:`/`Human:`/`Assistant:`), separator-line breakout (`---`), template/Jinja injection (`{{ }}`/`{% %}`), instruction-override keywords (ignore/forget/disregard/override), and code-execution attempts (`execute()`/`run()`/`eval()`), using 13 curated payloads in `tests/fixtures/injection_attempts/`. Also added `test_corpus_meets_minimum_size`, a guard so the suite can't silently pass if fixtures are deleted.

**Self-review confirmation:** [*] make check passes  [*] make test-unit passes
Neither passes cleanly, but only due to pre-existing issues unrelated to this branch: `make test-unit` has 53 pre-existing failures (verified via `git diff main --stat` that none of the failing files were touched here), and `make check` has pre-existing lint/type errors elsewhere (verified `ruff`/`black`/`mypy` are clean on every file this PR changes). The new `tests/security` suite passes 15/15.

**Draft PR feedback received from:** 
none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [*] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

No reviewer feedback has come in yet as of this check-in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

What was way harder than expected was understanding the codebase and specifically the safety layer, this is because it required me too see the codebase as a whole and verify what files were and were not included. For my issue, it required me to run a prompt injection test everytime a file in the safety layer was altered in a pull request so understanding which files fall under that category is key.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

Some of the things I learned about working in a large codebase is that there are very strict standards with naming, pull requests and making comments about code written in the project. Specifically with the pull request to merge the working branch, projects have their own specifif template and tags thats have to be followed exact to speed up the review process and convey to correct information to the reviewers.
**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

The assistance I received from Claude was very helpful during the review of the codebase and the research aspect of the prompt techniques. Understanding what parts of the codebase were in and touching the safety layer was alot more simple when I asked claude to make a diagram of the complete codebase. Futhermore, writing down the subtasks to complete the tasks definetly gave claude enough context to help write the edge cases I did not want to miss that would be iplmented in the ci.yml to handle all types of pull requests.

Where it fell short: Claude's first draft of the CI guard script (the bash logic comparing fixture and test counts against the base branch) actually had a bug — `grep -c` prints a count even when it exits non-zero on zero matches, and Claude's own fallback logic for handling that case ended up double-printing the count and breaking the numeric comparison. It only surfaced once we manually ran the script locally against real `git` refs to simulate different scenarios, so I learned that AI-generated shell logic still has to be actually executed and checked, not just read and trusted.
**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

Normally I would say choosing a different issue because choosing a tier 3 was alot of work, especially just understanding the codebase and creating my subtasks took way longer than the estimated time for the total project on the issue tracker. But after enjoying the outcome of this project, I would only change the planning because I would have perfered to make my plan and notes more detailed to make it easier to work after a couple days, especially in large issue where you need multiple days or weeks.
**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

I am proud that I was able to complete a tier 3 issue, I took it as a challenge because it was a cybersecurity related issue and thats the facet im building my career on. I did spend alot of time just to  be able to understand the issue and then spent alot less time fixing it. This issue gave me a brief look into how security is handled and and how protection against prompt injection might be iplemented into big codebases like this with payloads in a security fixture and a script with runs all the tests like "test_prompt_injection.py".
