## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** Tier 1

**Problem summary:**
`BiasDetector.detect_bias()` in `safety/bias_detector.py` relies on a small set of rigid regexes that only match near-exact phrase orderings (e.g. "bootcamp education is insufficient"), so it misses the same bias expressed in more natural phrasing, such as "bootcamp graduates can't write production code" or "young developers can't handle complex systems." As a result, 9 of the tests in `tests/unit/test_bias_detector.py` currently fail, meaning dismissive-education and demographic-assumption bias can slip past the safety layer undetected in generated feedback. A successful fix reworks the `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` regex lists (or the matching approach) to catch these common phrasing variations — covering verbs like "can't"/"lack"/"struggle" and subject variants like "developers"/"programmers"/"graduates" — while still passing the existing tests that assert neutral/positive mentions of bootcamps or educational background are not flagged.

**Branch name:** fix/151-bias-detector-too-narrow

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [commit link](https://github.com/Harsh-D20/pathreview/commit/a6de94d85f04585a36c050509589de238312f7c4)

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_bias_detector.py -v` and confirmed 9 of 32 tests fail exactly as described in the issue — e.g. `test_dismissive_bootcamp_language_detected` ("bootcamp graduates can't write production code") and `test_demographic_assumption_age_detected` ("young developers can't handle complex systems") both return `is_biased=False` because the existing regexes only match singular subjects and a narrow set of verb phrasings. Documented the root cause with an inline comment in `safety/bias_detector.py`.

**PLAN.md link:** [PLAN.md link](https://github.com/Harsh-D20/pathreview/blob/fix/151-bias-detector-too-narrow/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None currently — candidate regex patterns for both `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` were hand-validated against all 32 test assertions in a scratch script (0 mismatches) before writing PLAN.md, so the approach is de-risked going into implementation in Week 9. Still need to apply the patterns to `safety/bias_detector.py` itself and confirm against the real `pytest` run (scratch validation isn't a substitute for that).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented PLAN.md steps 1–3: rewrote `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` in `safety/bias_detector.py` to accept plural subjects (`developers`/`programmers`/`graduates`), broader verb phrasings (`can't`/`lacks?`/`missing`), and looser subject-verb ordering. Captured a `make check`/`make test-unit` baseline before the change, then re-ran both after and diffed the failing-test lists by exact test ID to confirm the 9 target tests now pass and no other test/lint/type-check result changed. Documented all of this in `PR_description.md`.

**Next steps:**
Commit the fix, `PLAN.md`, and `PR_description.md`; push; open the PR against `ascherj/pathreview`; do the manual sanity-check pass from PLAN.md step 4 on a few phrasings outside the test file to gauge generalization.

**Blockers:**
None technical. Nothing is committed/pushed yet — still need to do that before a PR link exists.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/786](https://github.com/ascherj/pathreview/pull/786)

**Branch:** `fix/151-bias-detector-too-narrow`

**What you built:**
Broadened the two `BiasDetector` regex pattern lists in `safety/bias_detector.py` to catch common real-world phrasings of dismissive-education and demographic-assumption bias (plural subjects, more verbs, looser word order) instead of only the exact phrase orderings the original regexes were written against — the public `detect_bias(text) -> (bool, str)` interface is unchanged.

**Tests added or updated:**
None added or modified — `tests/unit/test_bias_detector.py` (32 tests) was already the complete spec from the issue (9 of the 32 were failing); the fix's job was to make all 32 pass without touching the test file.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none