# PathReview Contribution Journal

My running record of Module 3 work on PathReview. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** Fixture too short: `test_readme_with_all_quality_signals` asserts `comprehensive` but README has ~51 words

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The unit test `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py`
expects a high-quality README to be scored as `comprehensive`, but the sample README embedded
in the test only contains about 51 words. The scorer in `agent/tools/readme_scorer.py` is
actually behaving correctly: it labels anything under 100 words as `minimal` and only calls a
README `comprehensive` once it reaches 500+ words. So the test asserts an outcome the fixture
data can never produce, and it fails even though the scorer logic is right the defect is in
the test's fixture, not the production code. A successful fix expands the fixture README to a
realistic length (500+ words) while preserving all of its quality signals (installation, usage,
badges, a demo link, and a tech-stack section), so every assertion passes and the suite
reflects the scorer's true behavior.

**"Is this right for me?" checklist reasoning:**

- **Scope is small and contained:** the change is limited to one fixture string in a single
  test file. No production or runtime code changes, no database, no API, and no frontend,
  so the risk of breaking unrelated behavior is very low.
- **I understand the root cause:** I can reproduce the failure locally (`assert 51 > 100`) and
  I've traced it to the word-count thresholds in the scorer, the fixture is simply too short
  for the `comprehensive` category (which needs 500+ words), not a scorer bug.
- **Effort fits Tier 1:** this is a self-contained test fix I can complete and verify with
  `make test-unit` and `make check` well within the module window — appropriate for a first
  contribution to a large codebase.
- **Clear done criteria:** success is unambiguous — the previously failing test passes and the
  rest of the `readme_scorer` suite stays green.

**Branch name:** `fix/156-readme-scorer-fixture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [REPRO_COMMIT_URL](https://github.com/sid-pandya/pathreview/commit/5e9df91223f4ddf453ff9c72e4b64bb8cee30e3d)

**Reproduction summary:**
I reproduced the bug by running the single failing test:
`.venv/bin/python -m pytest tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals -q`.
It fails at `assert data["word_count"] > 100` with `assert 51 > 100`, and the scorer logs
`category=minimal word_count=51`. This confirms the fixture README is only 51 words, so it can
never reach the `comprehensive` category (which requires >= 500 words) that the test asserts.
The scorer is behaving correctly; the defect is in the test fixture. (I also found and reverted
a stray uncommitted edit that had pasted notes into the fixture, pushing it to 101 words, which
still failed at `assert 'adequate' == 'comprehensive'` because 101 words is still below 500.)

**PLAN.md link:** https://github.com/sid-pandya/pathreview/blob/fix/156-readme-scorer-fixture/PLAN.md

**Walkthrough video (recommended):** not recorded (optional; may record and share in Slack)

**Blockers or open questions:**
None blocking. Open question: how far above 500 words to pad the fixture so it stays
`comprehensive` without becoming noisy. I will confirm the exact `str.split()` count by running
pytest rather than estimating, since code fences and markdown syntax also count as words.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix. All five PLAN.md sub-tasks are done. I rewrote the `readme` fixture in
`test_readme_with_all_quality_signals` (`tests/unit/test_readme_scorer.py`) into a realistic
README of 564 words (verified `str.split()` count by running the test) that keeps every quality
signal the test checks: Installation and Usage sections, three image badges, a "Live Demo" /
"try it" link, and a Tech Stack section. The test now reports `category=comprehensive`,
`word_count=564`, `overall_score=1.0`, and passes. The full `readme_scorer` suite is green
(23 passed), and `ruff` and `black` are clean on the changed file.

**Next steps:**
Open a draft PR early, request peer/mentor review in Slack, fill in the PR template completely,
then mark it ready for review and record the PR link in Check-in 2.

**Blockers:**
None. Note: the repo has ~52 pre-existing unit-test failures and many pre-existing lint/format
issues in unrelated modules (skill_extractor, tech_detector, structural_chunker). My change
touches only the readme_scorer test fixture and does not affect them.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/280

**Branch:** `fix/156-readme-scorer-fixture`

**What you built:**
I fixed a unit test that could never have passed. `test_readme_with_all_quality_signals` expects a
strong README to be scored as "comprehensive," but the sample README baked into the test was only
51 words, and the scorer only awards "comprehensive" at 500 words or more. So the test was set up
to fail no matter how correct the scorer actually was. I rewrote that fixture into a realistic
~560-word README that still carries every signal the test looks for (installation and usage
sections, image badges, a live-demo link, and a tech-stack section), so it finally checks the
behavior it was meant to. I didn't touch any production code, because the bug lived entirely in
the test data.

**Tests added or updated:**
Only `tests/unit/test_readme_scorer.py`. I left the assertions exactly as they were and just
replaced the fixture README so it genuinely satisfies them. That one test goes from failing to
passing, and the rest of the readme_scorer suite (23 tests in total) stays green.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

A quick note on what "passes" means here: this repo already had a lot of failing tests and lint
warnings before I started, so I used the "no new failures" bar. The unit suite went from 53
failing to 52 after my change, which means I fixed one test and broke nothing. Everything else
that is red was already red and is unrelated to my fix, and I called that out in the PR
description as well.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #280 during the window. (Reviewer feedback is not
an active part of the Summer 2026 cohort, so this is expected.) The PR is open and marked ready for
review with a complete description that documents the pre-existing failures so a future reviewer
has the context they need.

**How you responded:**
No changes were required since no feedback arrived. If a maintainer had asked, the most likely
requests would have been to trim the fixture README or to move the course-artifact files (JOURNAL,
PLAN) out of the PR, and I would have addressed those before marking it ready.

---

### Reflection

**What was harder than you expected?**
The actual fix was tiny; getting a working local environment was the hard part by a wide margin.
Before I could even reproduce the bug I had to dig out from a full disk, get Docker past a stuck
login screen, upgrade Node from 18 to 22 because Vite 8 crashed on a missing `styleText` export,
reinstall the frontend because a native rolldown binding was skipped by an npm optional-dependency
bug, and get past a peer-dependency conflict. Each error only revealed the next one. The one-line
idea ("make the fixture longer") took minutes; the plumbing around it took hours.

**What did you learn about working in a large codebase?**
The biggest shift from my own projects: I could not assume the repo was healthy. It already had 52
failing unit tests and a lot of formatting and type drift, so "passing" had to be redefined as "my
change introduces no new failures" (I proved it went from 53 failing to 52). That forced real
discipline: keep the diff surgical, resist fixing unrelated things, and document the baseline so a
reviewer can tell my change apart from the existing noise. I also learned to actually trace the
problem instead of trusting the obvious suspect. The failing test pointed at the scorer, but the
scorer was correct and the bug was in the test's own fixture data. Reading the real contract (the
scorer counts words with `str.split()` and only calls a README "comprehensive" at 500+ words)
mattered more than the code change itself.

**How did AI tools help, and where did they fall short?**
AI was most useful for moving quickly through an unfamiliar multi-module codebase and for
diagnosing the cascade of environment failures, where it consistently read the real error and
pointed at the next step. It also helped me structure PLAN.md and the journal, and explain what the
scorer's regexes actually required. Where it fell short was anything that needed real verification.
It could describe the bug, but I had to run the test to get the true numbers (51 words, and the
fact that code fences and markdown count as words under `str.split()`), and I had to re-run after
every change because at one point the fixture silently reverted and the image badges got deleted,
which quietly broke the test. AI also could not make the scope call for me, like deciding not to
commit the 54 files that `make check` reformatted. Running things and checking the result was the
part I owned.

**What would you do differently if you started over?**
First, I would run `make test-unit` and `make check` before writing any code, so I knew exactly
which failures were pre-existing from the start instead of discovering the baseline halfway
through. Second, I would never run `make format` / `black .` on a repo with this much drift, since
it rewrote 50+ files; `--check` shows the same problems without touching anything. Third, I would
keep the fix in a single clean commit and not let the working tree drift, because the fixture got
reverted once and cost me time re-applying and re-verifying it. The issue selection itself was
good: small, self-contained, and genuinely Tier 1.

**What are you most proud of?**
Landing a clean, honest, minimal PR inside a messy repo. Not the fixture rewrite itself, which is
modest, but the discipline around it: a one-file diff, a before/after number that proves the change
fixed one test and broke nothing, and a description that clearly separates my work from the repo's
pre-existing problems. That "make it easy for a reviewer to trust your change" habit feels like the
most transferable thing I take out of this module.
