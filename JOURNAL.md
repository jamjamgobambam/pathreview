# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bias detector currently relies on regular-expression patterns that expect very specific sequences of words. Because the patterns are too restrictive, the detector misses natural sentences that express educational-background or age-related assumptions, even when the meaning is biased. This affects the bias-detection logic and causes several expected cases in `tests/unit/test_bias_detector.py` to fail. A successful fix will broaden the relevant patterns so they recognize the documented phrasings without incorrectly flagging unrelated language.

**Selection notes — “Is this right for me?” reasoning:**
This issue has a focused scope because it primarily involves the bias detector and its related unit tests. The issue includes examples of currently missed language and identifies the tests that document the expected behavior, giving me a clear way to reproduce and verify the problem. I have experience with Python, regular expressions, unit testing, and an AI-bias analysis project, so the technical area is appropriate for me. The main risk is making the patterns too broad and introducing false positives, so I will review the existing implementation carefully and run the complete bias-detector test suite after making changes.

**Branch name:** `fix/151-bias-detector-patterns`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Note Reproduction

**Issue:** Bias detector patterns are too narrow to match common phrasings
**Issue link:** `https://github.com/ascherj/pathreview/issues/151`
**Branch:** `fix/151-bias-detector-patterns`

### Reproduction

From the repository root, I ran:

```bash
source .venv/Scripts/activate
python -m pytest tests/unit/test_bias_detector.py -q
```

The test suite returned **9 failed and 23 passed**. In the failing cases, `BiasDetector.detect_bias()` returned `(False, "")` for statements containing dismissive educational language or demographic assumptions.

For example:

```python
BiasDetector.detect_bias(
    "bootcamp graduates can't write production code"
)
```

Observed:

```python
(False, "")
```

Expected:

```python
(True, "Dismissive language about educational background")
```

The issue appears in `safety/bias_detector.py`, where the patterns in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` are too narrow to recognize common wording variations.

No production code was changed during reproduction.

