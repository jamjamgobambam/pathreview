## Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings —
https://github.com/ascherj/pathreview/issues/151

### Understand
`safety/bias_detector.py` has two regex lists, `DISMISSIVE_PATTERNS` (dismissive
comments about educational background — bootcamp/self-taught vs. university) and
`DEMOGRAPHIC_PATTERNS` (assumptions about age, immigration status, or socioeconomic
background). Each pattern encodes one exact phrase shape (e.g. "X education is
insufficient/inadequate/lacks"). Expected behavior: `detect_bias()` should flag any
reasonably common phrasing that expresses the same dismissive or demographic-
assumption meaning — which is exactly what `tests/unit/test_bias_detector.py`
encodes. Actual behavior: 9 of 29 tests fail because phrasings that don't fit the
rigid template slip through, e.g. "self-taught developers are not equal to
university graduates" (existing pattern only covers "self-taught IS not/never equal
to", not "developers are not equal to"), and "bootcamp attendance means inadequate
training" (no pattern covers "means" as the connecting verb at all).

### Map
- `safety/bias_detector.py` — the only file with logic to change (`DISMISSIVE_PATTERNS`
  and `DEMOGRAPHIC_PATTERNS` class attributes, and possibly the matching approach in
  `detect_bias()` if regex alternation gets unwieldy).
- `tests/unit/test_bias_detector.py` — already exists and already encodes the target
  behavior; the goal is to make all 29 tests pass without editing this file, not to
  add new tests.

### Plan
1. Catalog the 9 currently-failing tests and extract the exact phrase structure each
   one needs (done — see reproduction notes in `JOURNAL.md` and the code comment in
   `bias_detector.py`).
2. Broaden `DISMISSIVE_PATTERNS` to accept more connecting verbs/structures
   ("means", "equals", "is not equal to", subject-first phrasing like "developers
   are not equal to X") instead of the current fixed templates.
3. Broaden `DEMOGRAPHIC_PATTERNS` similarly — cover "developers from poor/rich/
   working-class backgrounds", "foreign/immigrant/international developers
   struggle/can't/won't", and reordered subject/verb phrasings.
4. Re-run `tests/unit/test_bias_detector.py` after each change; confirm all 29 pass,
   including the "not flagged" tests (no new false positives on neutral/positive
   feedback).
5. Run `make lint` / `make typecheck` per `CONTRIBUTING.md` before opening the PR in
   Week 9.

### Inputs & outputs
Input: arbitrary feedback text (`str`). Output: `tuple[bool, str]` —
`(is_biased, reason)`. The fix only changes pattern definitions (and possibly the
matching strategy inside `detect_bias()`); the function signature and return
contract stay the same.

### Risks & unknowns
- Broadening patterns risks false positives on legitimate feedback — several
  existing tests (e.g. "your bootcamp background shows strong fundamentals") must
  keep returning `False`, so patterns need to stay anchored to dismissive/assumption
  language, not just keyword co-occurrence.
- Some phrasings reorder subject and verb ("developers from poor backgrounds can't
  afford" vs. the current "person from poor background" shape) — regex alternation
  could grow unwieldy; still deciding whether a pure-regex fix (consistent with the
  existing code style) is enough or whether a keyword-proximity helper is warranted.
  Will decide once I see how many alternations the 9 failing cases actually need.
- Need to write patterns that generalize to the *meaning* the tests describe, not
  patterns fitted only to the literal 9 failing test strings.

### Edge cases
- Empty string / whitespace-only input must still return `(False, "")` (already
  passing — must not regress).
- Matching must stay case-insensitive (`test_case_insensitive_detection`).
- Text with multiple bias indicators should still return `True` on the first match
  (`test_multiple_bias_indicators`).
- Neutral/comparative statements that mention bootcamp or demographic terms without
  a dismissive judgment must remain unflagged (the largest risk area — several
  existing tests cover this directly).
