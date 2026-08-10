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

### Check-in 1 (mid-week)

**Current progress:** I implemented the fix in `safety/bias_detector.py`, completing all four sub-tasks from `PLAN.md`: I made the `is` optional and allowed a bare `lacks` in the dismissive education pattern, added negative-capability verbs (`can't`/`cannot`) and the `programmers` noun, made the demographic age pattern accept plural nouns, and added `from poor/rich/working-class` for plural subjects plus `lack` to the immigrant/foreign pattern. `reproduce_bias.py` now exits 0 and all 32 tests in `tests/unit/test_bias_detector.py` pass (previously 9 failed).

**Next steps:** Commit the fix with a Conventional Commit message, open a PR against `ascherj/pathreview`, request peer feedback, then finalize.

**Blockers:** None.

---

### Check-in 2 (end of week)

**PR link:** [PR #671](https://github.com/ascherj/pathreview/pull/671)

**Branch:** fix/151-bias-detector-patterns

**What you built:** I broadened the regex in `safety/bias_detector.py` so the bias detector matches common phrasings it previously missed (plural nouns like "developers", negative-capability verbs like "can't write", the verb "lack", and the "means inadequate" / "are not equal" constructions), while still not flagging positive or neutral mentions. This resolves the 9 failing unit tests.

**Tests added or updated:** No new tests were needed. The existing suite `tests/unit/test_bias_detector.py` already covered all 9 cases; my change makes them pass (32/32 in that file).

**Self-review confirmation:**

- [x] make check passes — no new failures introduced (181 pre-existing lint errors, none in `safety/bias_detector.py`, unchanged before and after my change)
- [x] make test-unit passes — no new failures introduced (2 pre-existing collection errors from `core/config.py` env vars, unrelated to this issue; `safety/bias_detector.py` tests pass 32/32 in isolation)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in before the end of the module. Per the Summer 2026 course note, reviewer feedback is not a feature this semester.

**How you responded:**
N/A. No feedback received.

---

### Reflection

**What was harder than you expected?**
Navigating the pre-existing test infrastructure failures was harder than I anticipated. Before I could confidently verify my fix, I had to establish a baseline by running `make check` and `make test-unit` up front to document that 181 lint errors and 2 collection errors in `core/config.py` existed before I touched anything. Without that baseline, I couldn't have clearly argued that my changes introduced no new failures. That kind of defensive documentation isn't something I naturally do when building my own projects, but it is mandatory when contributing to someone else's codebase.

**What did you learn about working in a large codebase?**
The biggest difference from my own projects is that you can't treat the entire codebase as yours to fix. The `core/config.py` Pydantic validation errors and the 181 ruff errors are legitimate problems, but they belong to other issues. Contributing responsibly means scoping your change tightly, proving your contribution is isolated, and documenting the pre-existing state clearly, rather than either ignoring the failures or going off-scope to fix them.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for two things: explaining what each regex pattern was actually doing in plain English, and quickly running test output to confirm whether a pattern fix was too broad or too narrow. Where it fell short was in making judgment calls. Reading edge cases like "bootcamp attendance means inadequate training" required me to reason through the intent of the detector myself, not just accept a generated pattern.

**What would you do differently if you started over?**
I would run `make check` and `make test-unit` on day one, before selecting an issue, rather than after. Knowing the pre-existing failure state early would have shaped how I scoped my reproduction steps and written my `PLAN.md` with more precision. I also would have opened the draft PR earlier in Week 9 instead of waiting until the fix was finalized, since early feedback is the whole point of a draft PR.

**What are you most proud of from this module?**
The standalone reproduction script (`reproduce_bias.py`). Writing a script that imports the actual project module and programmatically demonstrates the bug, rather than just pointing at a failing test, gave me a cleaner and more honest proof of the issue. It also made verification after the fix unambiguous, the script either exits 0 or it doesn't.
