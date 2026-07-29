## Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings — https://github.com/ascherj/pathreview/issues/151

### Understand

Root cause: the patterns were written against the exact wording of a handful of example sentences instead of the underlying subject/verb/object structure of the bias claim, so anything not in that literal word order slips through undetected.
 
**Expected:** biased phrasings that vary the verb ("can't", "lacks", "struggle", "won't") or the subject noun ("developers", "programmers", "graduates", plural vs. singular) around the same underlying claim should all be flagged, while neutral/positive/factual mentions of bootcamps or educational background should not be.

**Actual:** 9 of 32 tests in `tests/unit/test_bias_detector.py` fail because the regexes are too rigid:
- `DISMISSIVE_PATTERNS[1]` only matches singular `graduate|developer` + `lack|missing` + `rigor|fundamentals|proper training` — misses `can't write ...`, plural `developers`/`programmers`, and `"education lacks fundamentals"` (subject/verb order it wasn't written for).
- `DISMISSIVE_PATTERNS[3]` requires `self-taught|bootcamp` immediately followed by `is/never`, so `"self-taught developers are not equal to..."` (subject noun inserted before the verb) doesn't match.
- No pattern covers `"<subject> attendance means inadequate training"` (assumption vs. observation case).
- `DEMOGRAPHIC_PATTERNS[0]` only matches singular `developer|programmer`, missing plural `"young developers can't..."`.
- `DEMOGRAPHIC_PATTERNS[1]` only matches `"person from"|"coming from"`, missing `"developers from poor backgrounds"`.

### Map

- `safety/bias_detector.py` — `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` class attributes on `BiasDetector`. This is the only file that needs a code change.
- `tests/unit/test_bias_detector.py` — existing test suite (32 tests, 9 failing); no changes needed here, it's the spec the fix must satisfy. Used as the source of truth for validation.
- No other module calls into these two pattern lists directly.

### Plan

1. **Rewrite `DISMISSIVE_PATTERNS`** to key off subject/verb pairs rather than fixed phrases:
   - Broaden the "education/training is X" pattern to make `is` optional and let `lacks` take a trailing object (`bootcamp education lacks fundamentals`).
   - Add `programmers?` and `coding bootcamp` to the "graduates/developers lack/can't" pattern, and generalize the verb set to `can't|cannot|won't|will not|lacks?|missing` followed by any object.
   - Loosen the "X is not equal to Y" pattern to allow an optional subject noun between `self-taught|bootcamp` and `is/are` (`self-taught developers are not equal to...`).
   - Add a new pattern for `"<bootcamp|self-taught> attendance means insufficient/inadequate/..."` to catch the assumption-vs-observation case without flagging plain factual mentions of attendance.
2. **Rewrite `DEMOGRAPHIC_PATTERNS`** to accept plural subjects and broader subject sets:
   - `person|developers?|programmers?` (was singular-only) before `can't/cannot/won't/will not`.
   - `person|people|developers?|programmers?|coming` before `from poor/rich/working-class` (was `person from`/`coming from` only).
   - Keep the immigrant/international/foreign pattern, optionally extend to `programmers?` for consistency with the other patterns.
3. **Validate against the full existing test suite** (`.venv/bin/pytest tests/unit/test_bias_detector.py -v`) — all 32 tests, not just the 9 failing ones, must pass so the fix doesn't regress the neutral/positive cases.
4. **Manually sanity-check a few phrasings not in the test file** (e.g. "bootcamp grads can't handle scale", "developer from a working-class background") to gauge whether the broadened patterns generalize or were tuned to just the test strings.
5. **Run `make check`** (lint + format + typecheck) and commit as `fix(safety): broaden bias detector regex patterns to match common phrasings`.

### Inputs & outputs

- **Input:** a single string of generated feedback text (`text: str`)
- **Output:** `tuple[bool, str]` — `(is_biased, reason)` 
- **Change is confined to:** the regex literals inside `DISMISSIVE_PATTERNS` / `DEMOGRAPHIC_PATTERNS`

### Risks & unknowns

- **Regex is inherently pattern-matching against known phrasings** — broadening to fix these 9 tests doesn't guarantee every real-world phrasing of the same bias gets caught (e.g. "grads" instead of "graduates", contractions written without an apostrophe are already handled via `'?` but new abbreviations won't be). This is a known ceiling of a regex-based approach vs. a classifier/LLM-based check, out of scope for this fix.
- **False-positive risk when broadening subject/verb gaps** — e.g. allowing `lacks?(?:\s+\w+)?` as a trailing object is intentionally generic; need to confirm it doesn't fire on sentences like "bootcamp education lacks nothing but polish" (double negative) — not in the current test set, worth a manual check.

### Edge cases

- empty and whitespace is already handled by the function.
- Text containing neutral takes without the assumption itself (e.g. "your bootcamp background shows strong fundamentals", "your resume shows bootcamp attendance") must stay unflagged
