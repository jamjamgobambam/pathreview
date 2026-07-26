## Solution plan

**Issue:** [#151: Bias detector patterns are too narrow to match common phrasings](https://github.com/ascherj/pathreview/issues/151)

### Understand

The safety module's bias detector (`safety/bias_detector.py`) checks generated feedback for dismissive educational language and demographic assumptions. The issue is that the regular expression patterns are too rigid.

I programmatically reproduced the failures by writing a standalone script (`reproduce_bias.py`) that runs failing test cases directly through the `BiasDetector` class. This confirmed that the detector misses:

1. **Typographical bugs:** `DISMISSIVE_PATTERNS[0]` requires `is` before `lacks` (fails matching "bootcamp education lacks fundamentals").
2. **Missing capability verbs:** `DISMISSIVE_PATTERNS[1]` checks for `lack` or `missing` but misses negative capability phrasings like "can't write production code" and terms like `programmers`.
3. **Plural forms:** `DEMOGRAPHIC_PATTERNS[0]` matches singular nouns (`developer`/`programmer`) but misses plurals (`developers`/`programmers`).
4. **Demographic verbs:** `DEMOGRAPHIC_PATTERNS[2]` fails to match when the verb is `lack` (e.g. "immigrant developers lack fundamentals").

### Map

The following files are involved:

- [safety/bias_detector.py](file:///Users/tpl925_4/Desktop/CodePath/module-3/pathreview/safety/bias_detector.py) (holds the regex patterns to modify)
- [reproduce_bias.py](file:///Users/tpl925_4/Desktop/CodePath/module-3/pathreview/reproduce_bias.py) (the standalone reproduction script to verify outcomes)
- [tests/unit/test_bias_detector.py](file:///Users/tpl925_4/Desktop/CodePath/module-3/pathreview/tests/unit/test_bias_detector.py) (test suite to verify the fix)

### Plan

1. **Fix typos in `DISMISSIVE_PATTERNS`:** Adjust pattern 0 to make `is` optional before `insufficient|inadequate` and match `lacks` cleanly.
2. **Support capability verbs:** Expand pattern 1 to match negative capability phrasing (e.g., `can't\s+write`, `cannot\s+write`, `struggle\s+with`).
3. **Support plural forms:** Update pattern 0 in `DEMOGRAPHIC_PATTERNS` to handle plural variations (`developers?` and `programmers?` or `people|person`).
4. **Expand demographic verbs:** Update pattern 2 under `DEMOGRAPHIC_PATTERNS` to catch `lack` or `missing` as well as `can't|cannot|won't|struggle`.
5. **Verify changes:**
   - Run the reproduction script: `PYTHONPATH=. .venv/bin/python reproduce_bias.py` (which should now succeed and exit with code 0).
   - Run the unit tests: `.venv/bin/pytest tests/unit/test_bias_detector.py` to ensure all 32 tests pass.
   - Run `make check` to ensure formatting, linting, and type checking are clean.

### Inputs & outputs

- **Input:** Feedback string (`text`).
- **Output:** Tuple of `(is_biased: bool, reason: str)`.

### Risks & unknowns

- **False Positives:** Broadening patterns too much could mistakenly flag positive or neutral statements that reference non-traditional backgrounds (e.g., "your bootcamp background shows strong fundamentals"). I must balance regex flexibility with boundary constraints.

### Edge cases

- **Casing:** Handled via `re.IGNORECASE` in the detector.
- **Spacing/Hyphenation:** Words like "self-taught" or "working-class" must match with or without spaces/hyphens (e.g., `working[\s-]?class`).
