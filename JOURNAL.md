## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue highlights that the regex patterns in bias_detector.py are overly restrictive, causing the detection logic to miss common, natural-language variations of biased statements. Currently, standard phrasing regarding educational or demographic assumptions—such as remarking on a candidate's bootcamp background or age—fails to trigger the expected flags, resulting in nine failing unit tests in tests/unit/test_bias_detector.py. A successful fix would update or broaden these regex patterns so that BiasDetector.detect_bias() correctly flags natural variations of biased language while passing all nine associated test cases.

**Branch name:** fix/151-bias-detector-patterns-too-narrow

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger