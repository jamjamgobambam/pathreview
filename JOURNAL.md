## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [Yes] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, LLM prompt templates can be silently changed, which can heavily impact the quality of resume reviews. So, a test that will compare the current prompt template string to a stored prompt template string (a snapshot) should be made. 
If there are changes and the version was not adjusted accordingly, this snapshot test should fail. If there are changes and an updated version, the test should pass. If there are no changes and no version change, this test should pass. If there are no changes and a version change, my assumption is that this test should still fail for incorrectly bumping up the version.

**Branch name:** test/37-snapshot-tests-for-prompt-templates

**Setup confirmation:** [Yes] App runs locally at localhost:5173

**Cohort ledger:** [N/A] Issue added to cohort ledger (I am a TF)

---

### Reproduction/Confirmation of Issue:

Before (In bash, run "make test-unit" and check for test_prompt_templates.py):
![All passing tests for test_prompt_templates.py unit tests](image.png)
All the tests were passing for test_prompt_templates.py

After (after temporarily altering the prompt templates heavily without changing the version):
![All except test_skills_feedback_requests-json_format passed for test_prompt_templates.py unit tests](image-1.png)
Most tests for test_prompt_templates.py pass except a JSON format test. This is because I removed the entire section for the JSON format request in one of the prompt templates. Aside from this, the prompt template changes I made were nearly undetectable. Smaller, more subtle changes without version updates would be much harder to trace. This requires the need of another unit test.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/EshaM3/pathreview/commit/d290dad2d956a1cea513ad61a4a1296e9ce2b1c6

**Reproduction summary:**
I ran all the test_prompt_templates.py unit tests to see them all passing. Then, after temporarily removing a bunch of text, I ran it again to see all except one test still passing. This showed to me that such a big change was barely traceable, so this was a problem for even more subtle prompt template changes.

**PLAN.md link:** https://github.com/EshaM3/pathreview/commit/86874a512bbaa838572e6076a68a74a024c32216

**Blockers or open questions:**
Will need to think on how to make a script to generate a file, as I don't recall doing that before.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have completed all the subtasks from PLAN.md.

**Next steps:**
I will create and fill out the PR for this test enhancement.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/318

**Branch:** `test/37-snapshot-tests-for-prompt-templates`

**What you built:**
This PR replaces the "test_template_snapshot_content_hash" unit test with the new "test_template_version_update_snapshot" unit test. The new unit test calls on a script that can generate snapshots of the prompt templates if a snapshot does not already exist. And if there is a silent change made to any template without adding it as a new/updated version, then the test fails.

**Tests added or updated:**
`test_prompt_templates.py` was the test file I added to for this PR

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviews came in yet.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The planning part for the implementation still had gaps left to fill by the time I was implementing the solution. I guess when I was planning, I did not completely visualize the concrete, step by step process I would go through enough to see that some parts of the plan were missing. During the implementation phase, I had to fill in those gaps as I went, as well as reorder some of the steps for a more logical implementation. But thankfully, once I rearranged those and filled in the gaps midway through the implementation, everything else mainly fell into place.

**What did you learn about working in a large codebase?**
Definitely make sure to read documentation files like `CONTRIBUTING.md`, `SETUP.md`, `README.md` and `ARCHITECTURE.md` before planning any fixes or creating your branch. Not only do these files have helpful information that help you understand what is going on in this new, foreign codebase, but it will inform you of all the conventions required of all contributors to keep everything organized and running smoothly. Also, the UMPIRE method still applies here and is very useful for planning one's fix (especially with considering edge cases).

**How did AI tools help — and where did they fall short?**
It helped the most during the planning phase and the implementation phase. While planning, it provided some useful insight on how snapshots were usually generated with a separate script file that a snapshot test would call on, and that "hash codes" are what are generally used when generating snapshots so that one does not have to save large text blocks in the snapshot. This was quite useful for someone who has never even heard of a snapshot test before to implement it in a way that is both organized and expected by other contributors. It also brought up some edge cases I haven't thought of so that I could tweak my plan to better mitigate those. As for the implementation, it helped a lot with hash syntax and all of the file reading/writing syntax that was required to call a script, writing the generated snapshot as a new json file in a new directory, etc., as I was not very familiar with writing code for these processes before.

**What would you do differently if you started over?**
I would definitely try to take a bit more time with planning so that the order would be more logical and that there would be less gaps to fill during the implementation phase. Also, I would not run this command too quickly: `make format`, as it ended up correcting linting issues throughout the entire codebase (not part of the scope of the issue), which I had to partially undo due to how it would have crowded my PR with unrelated file edits.

**What are you most proud of from this module?**
I am proud of myself for implementing something I wasn't very familiar with nearly at all. I understood it conceptually, but I have never implemented it before. So, planning and implementing a fix with many file reading/writing components was an intimidating task that I am very happy correctly works!