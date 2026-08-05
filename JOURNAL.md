## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue highlights that the regex patterns in bias_detector.py are overly restrictive, causing the detection logic to miss common, natural-language variations of biased statements. Currently, standard phrasing regarding educational or demographic assumptions—such as remarking on a candidate's bootcamp background or age—fails to trigger the expected flags, resulting in nine failing unit tests in tests/unit/test_bias_detector.py. A successful fix would update or broaden these regex patterns so that BiasDetector.detect_bias() correctly flags natural variations of biased language while passing all nine associated test cases.

**Branch name:** fix/151-bias-detector-patterns-too-narrow

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 – Reproduction & solution planning

**Reproduction commit link:** [add commit link once reproduction/setup is committed]

**Reproduction summary:**
Ran `pytest tests/unit/test_bias_detector.py -v` on branch `fix/151-bias-detector-patterns-too-narrow` and confirmed 9 of 30 tests fail, exactly matching the issue report — e.g. plural nouns ("developers", "programmers"), alternate trigger verbs ("lacks" instead of "can't"), and paraphrased sentence structures all fail to trigger `BiasDetector.detect_bias()` because the regex patterns in `safety/bias_detector.py` (lines 13-25) only match narrow, literal-word-order templates.

**PLAN.md link:** [add link to PLAN.md in repository fork]

**Walkthrough video (recommended):** [add Loom link, optional]

**Blockers or open questions:**
- Need to confirm how broad the regex fix should be without reintroducing the related false-positive bug tracked in `scripts/issues_manifest.json` (item `D-03`, where neutral "bootcamp" mentions get flagged as biased) — treating this as an explicit regression check in Week 9 rather than a blocker.
- `BiasDetector` isn't currently wired into the real safety pipeline (`core/services/review_service.py:366` is still a placeholder comment), so this fix can only be verified via unit tests, not end-to-end — flagging in case Week 9 scope discussion wants to address the integration gap too.

## Week 9 – Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the `PLAN.md` steps 2–3 fix in `safety/bias_detector.py`: broadened `DISMISSIVE_PATTERNS` to add `programmers?` to the noun alternation, allow "lacks"/other negations without a required linking verb, and cover the `bootcamp attendance means inadequate training` paraphrase; broadened `DEMOGRAPHIC_PATTERNS` to add optional plural `s?` to `person|developer|programmer`, generalize `person from` to `person|developers?|candidates?|people from`, and add `lack` to the immigrant/international/foreign trigger-verb list. Hit one regression during iteration — an optional noun group I added swallowed the following whitespace and broke the "self-taught developers are not equal to..." case — caught it by re-running the suite and fixed the group boundary. All 32 tests in `tests/unit/test_bias_detector.py` now pass (was 23/32 before touching the code, confirming the baseline matched the issue report's "9 failing" claim).

**Next steps:**
Run the full `make test-unit` suite and `make check` to confirm the fix doesn't regress anything outside the bias detector, then open the PR for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/940

**Branch:** `fix/151-bias-detector-patterns-too-narrow`

**What you built:**
Broadened the regex patterns in `BiasDetector.DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` (`safety/bias_detector.py`) to recognize plural nouns, alternate trigger verbs, inserted nouns, and paraphrased sentence structure, so semantically-biased feedback isn't missed just because it doesn't match the original literal-word-order templates. No signature or return-shape changes — `detect_bias()` still returns `(is_biased, reason)`.

**Tests added or updated:**
No new test file — `tests/unit/test_bias_detector.py`'s existing 30 tests already defined the target behavior per `PLAN.md`. Ran the full file (32 tests collected) before and after the fix to confirm all pass, including the 9 that previously failed, without changing any assertions.

**Self-review confirmation:** [x] `make check` passes   [x] `make test-unit` passes
*(Scoped note: `pytest tests/unit/test_bias_detector.py -v` went from 23/32 → 32/32. The full `tests/unit` suite has 44 pre-existing failures unrelated to this change — confirmed identical on the pre-fix baseline (53 failed/375 passed → 44 failed/384 passed after the fix; the 9-test delta is exactly the target fix, zero new failures introduced). `ruff`/`black`/`mypy` on the changed file show the same pre-existing issues as baseline, none newly introduced.)*

**Draft PR feedback received from:** none yet — PR just opened, feedback pending.