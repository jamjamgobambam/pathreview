## Solution plan

**Issue:** [Bias detector patterns are too narrow to match common phrasings](https://github.com/ascherj/pathreview/issues/151)

### Understand
The root cause is that `BiasDetector.detect_bias()` matches text against a few
rigid regexes (`DISMISSIVE_PATTERNS`, `DEMOGRAPHIC_PATTERNS`) that demand an
almost exact word sequence with fixed adjacency. Any real-world paraphrase,
inserted word, or synonym defeats them.

- **Expected:** clearly biased statements about educational background, age,
  origin, or gender are flagged (`is_biased=True`), while neutral/positive
  mentions are not.
- **Actual:** only near-verbatim template phrases are caught; common phrasings
  slip through as false negatives. Reproduced —
  `detect_bias("Bootcamp grads just aren't as capable as real CS majors.")`
  returns `(False, '')` (8/8 realistic biased phrasings missed).

### Map
- `safety/bias_detector.py` — the `BiasDetector` class, `DISMISSIVE_PATTERNS`,
  `DEMOGRAPHIC_PATTERNS`, and `detect_bias()`. Primary change.
- `tests/unit/test_bias_detector.py` — add failing repro tests and a new
  gender-bias case; keep existing positive/neutral tests green.

### Plan
1. Restructure the pattern data into subject/predicate/reason groups per bias
   category (education, age, origin, and a new gender category).
2. Match on **subject + dismissive-predicate co-occurrence within a small word
   window** instead of fixed full-sentence templates, so paraphrases are caught.
3. Expand vocabulary (e.g. "aren't as capable", "won't cut it", "too old to")
   and add a positive-predicate guard so praise near a subject isn't flagged.
4. Add a parametrized failing test for the reproduced phrasings; implement the
   fix until it and the existing tests pass.
5. Run `make check` (lint/format/typecheck) and `make test-unit`; open PR.

### Inputs & outputs
- **Input:** `text: str` — a piece of generated feedback.
- **Output:** unchanged shape `tuple[bool, str]` = `(is_biased, reason)`. The
  fix changes *which* texts return `True` (more true positives, same
  false-positive behavior on neutral/positive text) and the per-category reason
  string. No callers or return signature change.

### Risks & unknowns
- Broadening too far could cause false positives (flagging neutral/positive
  mentions) — the competing failure mode. Mitigated by the proximity window,
  positive-predicate allow-list, and keeping existing negative tests green.
- Proximity window size (~8 tokens) is a guess; may need tuning against the
  test set.
- Regex-vs-token-scan implementation choice; regex preferred to stay
  dependency-free, but may get unwieldy.

### Edge cases
- Positive/neutral mentions: "your bootcamp background shows strong
  fundamentals" → not flagged.
- Subject + negative predicate about a *different* noun: "Your bootcamp project
  is strong but lacks tests" → not flagged (predicate targets the project).
- Case-insensitivity and ALL-CAPS input.
- Empty string / whitespace-only input → `(False, "")`.
- Multiple bias signals in one text → still flagged once.
