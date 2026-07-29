## Solution plan

**Issue:** [Bias detector patterns are too narrow to match common phrasings](https://github.com/ascherj/pathreview/issues/151)

### Understand
The root cause is in `BiasDetector.detect_bias()` in `safety/bias_detector.py`. The function only checks a small set of hard-coded regexes in `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS`, and those expressions are written for a few exact phrasings instead of the broader sentence shapes that appear in the tests. Because of that, the detector correctly catches phrases such as `bootcamp training is inadequate`, `self-taught is never comparable to university education`, `online course education is insufficient`, and some existing demographic phrasings, but it misses nearby variants like `bootcamp graduates can't write production code`, `coding bootcamp graduates can't write enterprise code`, `young developers can't handle complex systems`, `self-taught developers are not equal to university graduates`, `developers from poor backgrounds can't afford proper tools`, and `bootcamp attendance means inadequate training`.

Actual behavior from the reproduced test run is that `tests/unit/test_bias_detector.py` reports 9 failing tests and returns `False` for several statements that should be considered biased. The issue example also reproduces the same symptom: `BiasDetector.detect_bias()` returns `(False, "")` for language that should be flagged.

Expected behavior is that the detector should return `True` with the existing educational-bias reason string for dismissive educational background language, and `True` with the existing demographic reason string for demographic assumptions, while still returning `(False, "")` for positive, neutral, comparative-but-balanced, technical, and factual statements already covered by passing tests.

### Map
- `safety/bias_detector.py`
  The main implementation file and the most likely file to change.
- `BiasDetector`
  The class that owns the regex pattern collections and the detection entry point.
- `BiasDetector.detect_bias(text: str) -> tuple[bool, str]`
  The affected function. It iterates through the pattern lists in order and returns on the first match.
- `BiasDetector.DISMISSIVE_PATTERNS`
  Current regex collection for dismissive educational-background language. Likely needs to be expanded or regrouped.
- `BiasDetector.DEMOGRAPHIC_PATTERNS`
  Current regex collection for demographic assumptions. Likely needs to be expanded for plural and wording variants.
- `tests/unit/test_bias_detector.py`
  The verification file that defines the expected behavior. This file should not change for the fix, but it is the primary specification for the planned work.

Likely code changes are confined to `safety/bias_detector.py`, specifically the two regex collections and possibly small restructuring inside `detect_bias()` if pattern grouping or ordering needs to be clarified. No production call sites were identified as needing changes.

### Plan
1. Review each of the 9 failing tests and group them by missed sentence shape: dismissive educational claims, age-based assumptions, background-based assumptions, and observation-versus-assumption language.
2. Update `DISMISSIVE_PATTERNS` in `safety/bias_detector.py` to match broader but still targeted phrasings such as educational subject variants (`bootcamp`, `coding bootcamp`, `self-taught`, `attendance`) plus negative capability, inadequacy, or inferiority claims.
3. Update `DEMOGRAPHIC_PATTERNS` to cover singular and plural noun forms and alternate subject ordering, including cases like `young developers`, `developers from poor backgrounds`, and other already-tested background phrases.
4. Preserve the current return contract and reason strings in `detect_bias()` while checking whether the order of dismissive and demographic pattern evaluation needs adjustment for multi-indicator strings.
5. Re-run `tests/unit/test_bias_detector.py` to confirm the 9 reproduced failures pass without regressing the already-passing neutral, positive, factual, and technical cases.

### Inputs & outputs
The affected function is `BiasDetector.detect_bias(text: str)`, which accepts a single feedback string.

For biased educational-background text, the expected output is:
- `(True, "Dismissive language about educational background")`

For biased demographic-assumption text, the expected output is:
- `(True, "Demographic assumptions detected")`

For non-biased text, including empty strings, whitespace-only strings, positive references to bootcamp training, neutral references to bootcamp projects, factual observations like `your resume shows bootcamp attendance`, and ordinary technical feedback, the expected output is:
- `(False, "")`

The plan should preserve the existing reason strings exactly, because the tests already assert non-empty reasons and one test checks that the demographic reason contains `demographic`.

### Risks & unknowns
The main risk is making the regexes too broad. This issue area is especially sensitive because a naive wildcard around words like `bootcamp`, `self-taught`, `young`, or `poor` could start flagging positive, neutral, or factual statements that the current passing tests intentionally allow.

Another risk is wildcard matching with `.*` or overly permissive token gaps. That could let unrelated sentence fragments match across too much text, especially in multi-sentence feedback. Pattern precedence also matters because `detect_bias()` returns on the first match; if a generalized educational pattern becomes too loose, it might capture text before a more specific demographic pattern is evaluated.

Remaining unknowns include how far to generalize subject nouns like `graduates`, `developers`, `programmers`, and `backgrounds`; whether to normalize wording through regex alone versus light preprocessing; and whether phrases such as `means inadequate training` should be handled by a dedicated pattern instead of being folded into an existing education-dismissal pattern.

### Edge cases
- Capitalization: uppercase inputs such as `BOOTCAMP GRADUATES LACK FUNDAMENTALS` should still match through case-insensitive search.
- Punctuation: contractions and punctuation variants like `can't`, `doesn't`, and sentence-ending periods should not break detection.
- Singular/plural wording: patterns should cover `developer` and `developers`, `graduate` and `graduates`, `background` and `backgrounds`.
- Multiple bias indicators: strings like `young bootcamp graduates can't write code and immigrant developers lack fundamentals` should still return biased without depending on only one exact phrase.
- Neutral statements: text like `this bootcamp project demonstrates good coding practices` should remain non-biased.
- Positive statements: text like `your bootcamp training has given you a solid foundation` should remain non-biased.
- Factual statements: text like `your resume shows bootcamp attendance` should remain non-biased.
- Balanced comparisons: text like `Your bootcamp education covers practical skills. University education provides theory. Both have value.` should remain non-biased.
- Alternative wording: variants such as `coding bootcamp`, `self-taught developers are not equal to university graduates`, and `developers from poor backgrounds can't afford proper tools` need explicit coverage without matching every mention of those groups.
