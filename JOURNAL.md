## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:** The test test_readme_with_all_quality_signals in tests/unit/test_readme_scorer.py uses an inline fixture README that contains only ~51 words, but asserts word_count > 100 and word_count_category == "comprehensive". Looking at the scoring logic in agent/tools/readme_scorer.py, word counts are bucketed as "minimal" (<100), "adequate" (<500), or "comprehensive" (≥500), so the fixture actually needs to reach at least 500 words, not just past 100, for the assertion to hold. Currently the test fails not because of a scorer bug, but because the fixture content doesn't match what the assertions claim to validate. A successful fix extends the fixture README with enough realistic prose/content (while keeping all the quality signals: installation, usage, badges, demo link, tech stack) to legitimately cross the 500-word "comprehensive" threshold, so the test exercises the intended code path instead of asserting against under-sized input. This only touches the test fixture in tests/unit/test_readme_scorer.py—no production code in agent/tools/readme_scorer.py needs to change.

**Branch name:** test/156-extend-readme-fixture-word-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Is This Issue Right for Me? Checklist

### Part 1 — Understanding the Issue

- [x] **I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.**
  The test `test_readme_with_all_quality_signals` expects the sample README to have a high word count and be classified as `"comprehensive"`. However, the README fixture only has about 51 words, so it does not meet the scorer's requirements. The scoring logic is working correctly—the test data just needs to be updated.

- [x] **I've located the relevant files and confirmed they exist in the codebase.**
  I found both `tests/unit/test_readme_scorer.py`, which contains the failing test, and `agent/tools/readme_scorer.py`, which contains the README scoring logic.

- [x] **I can describe a concrete before-and-after.**
  Before, the test fails because the README fixture is too short to be considered `"comprehensive"`. After extending the fixture to more than 500 words, the test should pass while correctly testing the intended behavior.

### Part 2 — Tier Fit

- [x] **Tier is a realistic match for where I am.** Selected **Tier 1**.
  This issue only requires updating a test fixture in one file without changing any production code, so it fits the scope of a Tier 1 task.

### Part 3 — Codebase Readiness

- [x] **I've found and read the specific code the issue references.**
  I read the `_score_readme` function in `agent/tools/readme_scorer.py` and confirmed that a README needs at least 500 words to be classified as `"comprehensive"`.

- [x] **I understand the surrounding code well enough to write a rough plan.**
  My plan is to expand the README fixture so it passes the 500-word threshold while keeping the existing sections, badges, demo link, and other content the test already checks.

- [x] **I've read the relevant test file, end-to-end for at least one test.**
  I read the `TestReadmeScorer` test file, including the failing test and the other word-count tests, to understand how the scorer is expected to behave.

### Part 4 — Scope and Time

- [x] **Claims/crowding check.** I didn't find any open blockers or competing work on the issue.
- [x] **Scope is realistic for Weeks 8–9.** This should take about 1–2 hours since it's only a test fixture update and running the tests afterward.
- [x] **No open blockers or dependencies.** The issue can be completed independently.

### Selection Notes — Scope Reasoning

I chose this issue because it is small, well-defined, and only involves updating a test fixture instead of modifying the actual scoring logic since this is my first time. The main thing to watch out for is making sure the README reaches the correct 500-word threshold, since adding just enough words to get over 100 would still cause the test to fail.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SarahMa12/pathreview/commit/7762bc7bbaee1e4376746b28e08b5485b1b90c85

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_readme_scorer.py -v -k test_readme_with_all_quality_signals` locally and confirmed the test fails every time: the inline fixture README is only 51 words, so `assert data["word_count"] > 100` fails immediately  before the test even reaches the `word_count_category == "comprehensive"` check. Scorer output (`category=minimal score=0.87 word_count=51`) confirms the scoring logic itself is working correctly.

**PLAN.md link:** https://github.com/SarahMa12/pathreview/blob/test/156-extend-readme-fixture-word-count/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed the fix in `PLAN.md` by expanding the README test fixture in `tests/unit/test_readme_scorer.py` from about 50 words to over 500 words. I kept all the existing quality signals, including the installation and usage code blocks, badges, demo link, and tech stack, while adding more realistic content. I ran `tests/unit/test_readme_scorer.py`, and all 23 tests now pass. The previously failing test now reports a `"comprehensive"` word count category with a score of over 0.99.

**Next steps:**
Add tests for the exact word count boundaries (0, 1, 99, 100, 499, 500, 501, and 1000 words) to make sure the scorer correctly classifies README files as `"minimal"`, `"adequate"`, or `"comprehensive"` at each cutoff. After that, open the PR with the reproduction and plan links from Weeks 7–8 and include this fix.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/832

**Branch:** `test/156-extend-readme-fixture-word-count`

**What you built:**
The test `test_readme_with_all_quality_signals` expected the README fixture to be over 100 words and classified as `"comprehensive"`, but the fixture was only about 50 words, so the test failed even though the scoring logic was correct. I expanded the fixture to over 500 words so it meets the scorer's "comprehensive" threshold while still including all the quality signals the test checks (installation, usage, badges, demo link, and tech stack). No production code was changed.

**Tests added or updated:**
Updated only `tests/unit/test_readme_scorer.py` by expanding the README fixture from about 50 words to over 500 words. I didn't have time to add the planned boundary tests (0, 1, 99, 100, 499, 500, 501, and 1000 words), so that can be done in a future PR.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
These aren't fully passing on this branch because there are existing unrelated issues (`make lint`, `make typecheck`, and `make test-unit`). However, `tests/unit/test_readme_scorer.py` passes all 23 tests.

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
n/a

**How you responded:**
n/a

---

### Reflection

**What was harder than you expected?**
Even though the fix was small and only changed one file, understanding the codebase took longer than I expected. There were a lot of folders and files, so it wasn't clear which ones mattered. I started with the failing test, followed it to the scoring code, and made sure nothing else depended on the same logic before making any changes.

**What did you learn about working in a large codebase?**
I learned that it's better to start with the failing test instead of trying to understand the whole project. Following the error message and searching for specific code helped me find the right files much faster. Running the test first also showed me that the scoring code was correct and the test data was the real problem. Reading the rest of the test file helped me understand the pattern and avoid breaking other tests.

**How did AI tools help — and where did they fall short?**
AI helped me find the right files and explain how the scoring worked, which saved a lot of time. It also helped me write the longer README fixture once I knew what was needed. However, I still had to decide whether the issue was really just a test problem, make sure the new fixture made sense, and run the tests myself to confirm everything worked.

**What would you do differently if you started over?**
I would spend less time trying to understand the entire codebase and instead focus on the failing test right away. I would also add the boundary-value tests during the same PR instead of leaving them for later.

**What are you most proud of from this module?**
I'm most proud of completing my first "real" pull request in someone else's production codebase. I found the real cause of the problem, kept the fix small and focused, and successfully fixed the issue without changing the production code.