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