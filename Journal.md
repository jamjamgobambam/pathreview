## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
From what I understand, the README is expected to be long enough for the test to work but the one used in the sample is too short, hence the test will fail, even though the scoring logic is correct

**Branch name:** test/156-readme_scorer_test_fixture_too_short

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** Put in as a screenshot in the root of the project.

**Reproduction summary:**
At first, I couldn't get the test to run, but then I used Chat to give help me. I then ran `pip install structlog` and then I was able to reproduce the error by running `pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -q`. 

The test failed because the sample README used in the fixture has a `word_count` of 51, while the test asserts `word_count > 100`, causing a single failing assertion even though the scorer returns a valid overall score.

I observed that there were 22 tests that passed and then 1 test that failed which was the test on the word count of the 

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** readme_bug_reproduction.png (root of repository) or 
https://github.com/EkeneAni/pathreview/blob/test/156-readme_scorer_test_fixture_too_short/readme_bug_reproduction.png


**PLAN.md link:** It's in the root of the directory

**Walkthrough video (recommended):**
None

**Blockers or open questions:**
- Nothing at the moment

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md (Option A): extended the README fixture in `test_readme_with_all_quality_signals` from ~51 words to >500 words so it is legitimately categorized `comprehensive`, keeping all quality signals (installation, usage, badges, demo, tech stack) intact. Scorer logic left unchanged. All 23 tests in `test_readme_scorer.py` pass. Committed on `test/156-readme_scorer_test_fixture_too_short` and reworded to follow Conventional Commits (`test(agent): ...`).

**Next steps:**
Push the branch, open the PR against `ascherj/pathreview`, and request peer review. Decide whether the PLAN.md / Journal.md / screenshot artifacts stay in the PR.

**Blockers:**
None. (Because the `gh` CLI isn't installed, so opening the PR was via the GitHub web UI instead.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/679

**Branch:** `test/156-readme_scorer_test_fixture_too_short`

**What you built:**
Extended the unit-test README fixture so its word count exceeds the scorer's 500-word `comprehensive` threshold, resolving the failing assertion without changing scorer behavior. The bug was in the test fixture, not the scoring logic.

**Tests added or updated:**
Updated `tests/unit/test_readme_scorer.py` — the fixture in `test_readme_with_all_quality_signals`. It covers a full-signal README returning a high `comprehensive` score. All 23 tests in the file pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> Interpreted per course guidance: the change introduces **no new failures**. Both commands have pre-existing repo-wide failures (364 ruff errors; 53 unit failures) unrelated to this issue — identical before and after my change. `test_readme_scorer.py` itself passes ruff cleanly and all its tests pass.

**Draft PR feedback received from:** none

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review on my PR as of yet

**How you responded:**

---

### Reflection

**What was harder than you expected?**
- Firstly, I wanted to run the test_readme_scorer function in the unit folder but I couldn't because pytest was failing so I asked Copilot to run it for me instead and it found the issue, I needed to install structlog, so I did and I was able to run it. So getting the tests to run was harder than I thought.

**What did you learn about working in a large codebase?**
- Something I learnt from this project specifically is to record error counts before and after implementing a fix so that I can see that the fix was helpful, rather than just hoping it was.

**How did AI tools help — and where did they fall short?**
- AI assistance was most useful when I was running the tests. As I said previous;y, I couldn't get the pytest to run so I had to consult AI, more specifically Copilot, which helped me. I think AI fell short in explaining the issue of what went wrong in why I couldn't run the tests, which in all really isn't its fault.

**What would you do differently if you started over?**
- I would forst capture baseline test/lint failure counts at the start of an issue so "no new failures" is a measured claim.

- Install `gh` so PR work stays in the terminal instead of the web UI.

**What are you most proud of from this module?**
- That I finished. Prior to this I didn't know what a PR was or how to open one or even got an inkling of working in a large codebase but I would say that I really think I have at the very least a decent understanding of what is expected of me and that I can explain my issue and steps I took to implement the solution.