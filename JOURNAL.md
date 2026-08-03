## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** #151: Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The safety module's bias detector (`safety/bias_detector.py`) uses strict, narrow regular expression patterns to flag biased or dismissive language. Because of this, it fails to match common phrasings (such as plural developer terms, verbs like "can't write" for bootcamps, or missing/incorrectly structured optional matches). A successful fix will expand and generalize these regex patterns so they correctly capture all variations tested in the test suite without triggering false positives on positive or neutral statements.

**Branch name:** fix/151-bias-detector-patterns

**Setup confirmation:** [x] App runs locally at `localhost:5173`

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [[Link to reproduction commit](https://github.com/LilRed92/pathreview/commit/a7b287dbf643c6b402735f39bbe9bdae1f269d02)]

**Reproduction summary:**
I reproduced the issue programmatically by creating a standalone script (`reproduce_bias.py`) that imports `BiasDetector` and runs failing phrasings (such as plural developer forms and capability verbs) directly through it. The script confirmed that the current regex patterns miss these cases. I also added a TODO warning comment in `safety/bias_detector.py` to document this.

**PLAN.md link:** [[Link to PLAN.md](https://github.com/LilRed92/pathreview/blob/fix/151-bias-detector-patterns/PLAN.md)]

**Walkthrough video (recommended):** [[Link to walkthrough video](https://www.loom.com/share/de030fd88b424fc787dc7a8db6549b51)]

**Blockers or open questions:**
None. The reproduction script isolates the exact pattern failures, making testing and verification highly reliable.

## Week 9 — Solution building & PR submission

#### Check-in 1 (mid-week)

***Current progress:*** I implemented the fix in `safety/bias_detector.py`, completing all four sub-tasks from `PLAN.md`: I made the `is` optional and allowed a bare `lacks` in the dismissive education pattern, added negative-capability verbs (`can't`/`cannot`) and the `programmers` noun, made the demographic age pattern accept plural nouns, and added `from poor/rich/working-class` for plural subjects plus `lack` to the immigrant/foreign pattern. `reproduce_bias.py` now exits 0 and all 32 tests in `tests/unit/test_bias_detector.py` pass (previously 9 failed).
***Next steps:*** Commit the fix with a Conventional Commit message, open a PR against `ascherj/pathreview`, request peer feedback, then finalize.
***Blockers:*** None.

---

#### Check-in 2 (end of week)

***PR link:*** [PASTE_PR_LINK_AFTER_OPENING]
***Branch:*** fix/151-bias-detector-patterns
***What you built:*** I broadened the regex in `safety/bias_detector.py` so the bias detector matches common phrasings it previously missed (plural nouns like "developers", negative-capability verbs like "can't write", the verb "lack", and the "means inadequate" / "are not equal" constructions), while still not flagging positive or neutral mentions. This resolves the 9 failing unit tests.
***Tests added or updated:*** No new tests were needed. The existing suite `tests/unit/test_bias_detector.py` already covered all 9 cases; my change makes them pass (32/32 in that file).
***Self-review confirmation:***
- [x] make check passes — no new failures introduced (181 pre-existing lint errors, none in `safety/bias_detector.py`, unchanged before and after my change)
- [x] make test-unit passes — no new failures introduced (2 pre-existing collection errors from `core/config.py` env vars, unrelated to this issue; `safety/bias_detector.py` tests pass 32/32 in isolation)
***Draft PR feedback received from:*** none

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

**Next steps:**
[What are you working on for the rest of the week?]

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
