## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159#issue-4884927126

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

I chose a Tier 1 because this is my first time contributing to open source, so I wanted to practice going through the motions of the entire process without too many bumps on the road. I will like to try a second issue pending time.

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the test isn't passing for tests that test for presence of logs in caplog like in test_empty_chunks_list_return_empty in test_batch_processor.py.
We know that it's that issue because because in this example, the second assert is failing, which isolates the issue to lack of logs present in caplog.
So, even though the process functions correctly returns an empty list when there are no chunks,
and the empty list event is caputured (log seen in stderr), caplog isn't receiving the log.

The file I will look at will be tests/conftest.py because that's where test setup is configured,
and since both structlog and the business logic are working, it wouldn't make sense to check the running code.

A successful fix would mean that the caplog related tests pass.

**Branch name:** fix/159/structlog-output-not-captured

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/4cd813b86a3479a449fa372a5e759cbd07d2f8ac

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I first did a control -F project wide to see if the caplog issue existed anywhere else, but confirmed it was just in test_empty_chunks_list_returns_empty in tests/test_batch_processor.

1. Ran the test
2. Confirmed the test failed for the assert checking caplog for the log

**PLAN.md link:** https://github.com/ninaony/pathreview/blob/fix/159/structlog-output-not-captured/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I have not completed anything so far, so nothing has been finished yet

**Next steps:**
[What are you working on for the rest of the week?]
I'm working on the rest of the sub-tasks

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
