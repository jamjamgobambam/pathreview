# Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings — `https://github.com/ascherj/pathreview/issues/151`

### Understand

The root cause is that the regular expressions in `safety/bias_detector.py` require biased statements to follow narrow and nearly exact sequences of words.

For example, some patterns require an educational term such as `bootcamp` to be immediately followed by `graduates` or `developers`, followed by a limited verb such as `lack`. As a result, the detector misses equivalent statements that use `can't`, include words between the relevant phrases, use alternatives such as `programmers`, or describe the assumption in a longer sentence.

The demographic patterns have similar restrictions. They detect phrases such as “young developers can't,” but they do not consistently recognize other age-related constructions or plural background descriptions.

Expected behavior:

* Statements that dismiss a candidate based on educational background or make demographic assumptions should return `True` with the appropriate reason.
* Positive, factual, neutral, and technical feedback should continue returning `False` with an empty reason.

Actual behavior:

* Nine tests in `tests/unit/test_bias_detector.py` fail because biased statements are returned as `(False, "")`.

### Map

The following files are involved:

* `safety/bias_detector.py`

  * Contains `BiasDetector`.
  * Contains `DISMISSIVE_PATTERNS`.
  * Contains `DEMOGRAPHIC_PATTERNS`.
  * Contains the `detect_bias()` method that applies the regex patterns.

* `tests/unit/test_bias_detector.py`

  * Documents the expected biased and unbiased behavior.
  * Contains the nine currently failing test functions.
  * Contains positive and neutral cases that must remain unflagged.

Expected implementation changes will primarily be made in `safety/bias_detector.py`. The existing test file will be used for verification and may receive an additional regression case if the exact longer sentence from Issue #151 is not already represented.

### Plan

1. Group the nine failing tests by the type of language they represent: bootcamp or self-taught dismissal, age assumptions, socioeconomic-background assumptions, and combined bias indicators.

2. Compare each failing sentence with the current patterns in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` to identify the missing subjects, verbs, contractions, plurals, and allowable words between key phrases.

3. Expand or reorganize the regex patterns in `safety/bias_detector.py` so they allow common natural-language variations without relying on unrestricted expressions that could match unrelated text.

4. Run `tests/unit/test_bias_detector.py` after each pattern group is updated. Confirm that all nine previously failing tests pass and that the positive, neutral, factual, empty-string, and technical-feedback cases remain unflagged.

5. Run the complete unit test suite and project checks to confirm that the change does not affect other safety behavior:

```bash
make test-unit
make check
```

### Inputs & outputs

Input:

* A string containing generated portfolio feedback passed to `BiasDetector.detect_bias(text)`.

Output for biased feedback:

```python
(True, "Dismissive language about educational background")
```

or:

```python
(True, "Demographic assumptions detected")
```

Output for unbiased feedback:

```python
(False, "")
```

The fix should change which natural-language statements are recognized, but it should not change the method signature, tuple structure, or existing reason strings.

### Risks & unknowns

* Broadening the patterns in `safety/bias_detector.py` too much could flag positive or neutral references to bootcamps, self-taught developers, education, age, immigration, or socioeconomic background.

* Using an unrestricted `.*` between keywords could allow one part of a long sentence to match an unrelated part later in the text. The patterns should use bounded or clearly related phrase structures where possible.

* Multiple bias indicators may appear in one statement. Because `detect_bias()` returns after the first match, pattern ordering may determine which reason is returned.

* Contractions and related negative forms such as `can't`, `cannot`, `won't`, `lack`, `lacks`, and `inadequate` may require separate alternatives.

* It is still necessary to determine whether the issue can be solved cleanly by expanding the existing regex lists or whether small reusable regex components would make the implementation clearer and less repetitive.

### Edge cases

The fix should handle the following cases gracefully:

* Uppercase and mixed-case input.
* Empty or whitespace-only strings.
* Punctuation between relevant phrases.
* Additional descriptive words between the educational or demographic term and the negative assumption.
* Singular and plural words such as `developer`, `developers`, `programmer`, `programmers`, `background`, and `backgrounds`.
* Variants including `bootcamp`, `coding bootcamp`, `self-taught`, and `online course`.
* Negative forms including `can't`, `cannot`, `won't`, `will not`, `lack`, `lacks`, and `inadequate`.
* Statements containing more than one bias indicator.
* Positive, factual, balanced, and neutral discussions of educational or demographic backgrounds, which must not be flagged.
