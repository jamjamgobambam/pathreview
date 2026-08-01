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