## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** Tier 1

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that there is a readme scorer that is hardcoded to have the readme's word count greater than 100 words and word_count_category = "comprehensive". But our readme only has 51 words. So, I need to either increase the word count or fix the readme scorer from minimum 100 words to something like 50 so that our readme passes the test.

**Branch name:** fix/156-readme-scorer-fixture-length

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/oasis-pandey/pathreview/commit/47727a29aa10a668275a48f2db2b56fa5737d07f

**Reproduction summary:**
I reproduced the issue by running `pytest tests/unit/test_readme_scorer.py -q`. The test failed at `assert data["word_count"] > 100` because the fixture README only produced a word count of 51, which confirms the fixture is too short for the assertion.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #156. Expanded the README test fixture in
`tests/unit/test_readme_scorer.py` from ~51 words to 500+ words so it meets
the scorer's "comprehensive" threshold (≥ 500 words). The fixture now
includes realistic sections: project description, installation, usage,
features, tech stack, badges, demo link, API reference, architecture,
contributing, testing, deployment, and license. Updated the word_count
assertion from `> 100` to `> 500` to match the scorer's actual boundary.
All sub-tasks from PLAN.md are done.

**Next steps:**
Open draft PR, request peer feedback, finalize and submit PR.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/472

**Branch:** `fix/156-readme-scorer-fixture-length`

**What you built:**
Expanded the test fixture in `test_readme_with_all_quality_signals` to be a
realistic, comprehensive README with 500+ words. This fixes the mismatch
between the test's assertions (`word_count > 100`, `word_count_category ==
"comprehensive"`) and the scorer's actual logic (which requires ≥ 500 words
for "comprehensive"). No changes were made to the scorer implementation — the
fix is entirely in the test file.

**Tests added or updated:**
Updated `tests/unit/test_readme_scorer.py` — specifically the
`test_readme_with_all_quality_signals` test method. The expanded fixture now
correctly exercises the "comprehensive" word-count category and all quality
signal detections (installation, usage, badges, demo link, tech stack). All
23 tests in the file pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Pre-existing failures observed (not introduced by this change):
- `make check`: 182 ruff errors and mypy type errors across multiple files
  (test_review_service.py, test_security.py, test_semantic_chunker.py,
  test_skill_extractor.py, test_structural_chunker.py, test_tech_detector.py).
  None are in test_readme_scorer.py. The ruff and mypy checks on
  test_readme_scorer.py pass cleanly.
- `make test-unit`: 52 pre-existing failures across other test files
  (test_batch_processor, test_bias_detector, test_faithfulness_checker,
  test_keyword_search, test_output_parser, test_pii_scrubber,
  test_prompt_defense, test_readme_parser, test_relevance_scorer,
  test_resume_parser, test_review_service, test_security,
  test_skill_extractor, test_structural_chunker, test_tech_detector).
  My change introduces zero new failures and fixes the 1 pre-existing
  failure in test_readme_scorer.py (now 23/23 pass).

**Draft PR feedback received from:** [to be updated]