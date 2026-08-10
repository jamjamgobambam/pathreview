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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
no review

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Getting the regex broad enough to catch the 9 missing phrasings without drifting into false positives on the neutral/positive test cases was a genuine balancing act, not the mechanical find-replace I expected going in. Every time I widened a subject or verb alternation, I had to re-check it against sentences like "your bootcamp background shows strong fundamentals" that share keywords with the biased phrasings but aren't biased.

**What did you learn about working in a large codebase?**
I learned to map effects before touching shared code. Before editing the pattern lists I confirmed no other module reaches into `DISMISSIVE_PATTERNS`/`DEMOGRAPHIC_PATTERNS` directly, which meant the change was safely contained to one file and its return signature couldn't be assumed correct without checking.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for cheap experimentation: instead of editing the real file and re-running pytest over and over, I had Claude write a standalone scratch script with all 32 test assertions hardcoded and iterate on the regex patterns there first, catching mismatches before they ever touched `safety/bias_detector.py`. It also caught the "before/after" testing discipline for me — diffing exact failing-test IDs rather than just comparing counts. Where it fell short was anything requiring a judgment call only I could make: it explicitly stopped and asked rather than guessing when the PLAN.md planning framework wasn't actually in my message, and again before pushing/committing to the branch.

**What would you do differently if you started over?**
I would investigate semantic checking systems. Due to time and novelty, I didn't go into that rabbit hole, but it is something worth considering since Regex has a known ceiling in its effectiveness. 

**What are you most proud of from this module?**
The validation discipline, not the fix itself — hand-testing the candidate patterns against all 32 assertions before touching the real file, then diffing the exact failing-test IDs before and after the change to back up "no new failures" with evidence instead of a visual skim of pytest output. I was proud to be able to direct Claude and reproduce its work in order to make sure my work did not actually change anything currently not in my issue's scope.