## Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings — #151
(https://github.com/ascherj/pathreview/issues/151)

### Understand
**Root cause.** `BiasDetector.detect_bias()` in `safety/bias_detector.py` relies on two
lists of regexes (`DISMISSIVE_PATTERNS`, `DEMOGRAPHIC_PATTERNS`) that require near-exact
phrase sequences, so natural rephrasings of the same bias never match. Three specific
narrowness bugs:

- **Hardcoded connectors.** The dismissive education pattern is
  `(?:education|training)\s+is\s+(?:insufficient|inadequate|lacks)` — it demands the word
  "is", so "bootcamp education **lacks** fundamentals" (no "is") slips through.
- **Singular-only subjects.** Patterns match `developer`/`graduate`/`programmer` but not
  their plurals, so "young **developers** can't…" and "bootcamp **graduates** can't…"
  don't match.
- **Fixed subject anchors.** The demographic background pattern only anchors to
  `person from` / `coming from`, so "**developers** from poor backgrounds can't…" is missed.

**Expected vs. actual.** `detect_bias()` should return `(True, <reason>)` for dismissive
educational-background language and demographic assumptions across common phrasings.
Actual: it returns `(False, '')` for these phrasings. **9 of 32** unit tests fail.

### Map
Which files, functions, or modules are involved:

- **`safety/bias_detector.py`** — the only file to edit. Specifically the
  `DISMISSIVE_PATTERNS` list (lines 13–18), the `DEMOGRAPHIC_PATTERNS` list (lines 21–25),
  and the `detect_bias()` static method (lines 27–51).
- **`tests/unit/test_bias_detector.py`** — reference only, not edited. The 9 failing tests
  define the target phrasings; the `*_not_flagged` tests (e.g.
  `test_positive_bootcamp_mention_not_flagged`, `test_neutral_bootcamp_mention_not_flagged`,
  `test_comparative_without_bias`) are precision guardrails that must stay green.

The 9 failing tests to satisfy: `test_dismissive_bootcamp_language_detected`,
`test_bootcamp_lacks_rigor_detected`, `test_demographic_assumption_age_detected`,
`test_coding_bootcamp_variant`, `test_developer_vs_programmer_distinction`,
`test_multiple_bias_indicators`, `test_negative_educational_claim`,
`test_rich_poor_assumption`, `test_assumption_vs_observation`.

### Plan
Concrete sub-tasks:

1. **Broaden the dismissive-subject patterns.** Allow plural subjects
   (`graduates?`, `developers?`, `programmers?`) and negative predicates that don't require
   "is" — e.g. `can'?t`/`cannot` + write/handle/afford, and `lacks?`. Covers
   "bootcamp graduates can't write production code" and "bootcamp programmers lack proper
   training".
2. **Handle the `coding bootcamp` variant and the "…are not equal/comparable to…" phrasing.**
   Covers "coding bootcamp graduates can't write enterprise code" and "self-taught
   developers are not equal to university graduates".
3. **Drop the hardcoded "is" in the education pattern** so "bootcamp education lacks
   fundamentals" / "bootcamp attendance means inadequate training" match.
4. **Broaden the demographic patterns.** Match plural demographic nouns and alternative
   subject anchors ("developers from poor backgrounds", not just "person from"), and age
   assumptions with plural subjects ("young developers can't…").
5. **Add precision guards.** Require a negative predicate near the keyword so positive/
   neutral mentions of "bootcamp" stay unflagged. Keep the demographic branch's `reason`
   containing the word "demographic" (asserted by `test_demographic_assumption_age_detected`).
6. **Verify.** Run `make test-unit` (or `.venv/bin/python -m pytest
   tests/unit/test_bias_detector.py -v`) until 32/32 pass, then `make check`
   (black + ruff + mypy).

### Inputs & outputs
- **Input:** `text: str` — the feedback string to scan (unchanged).
- **Output:** unchanged signature `tuple[bool, str]` = `(is_biased, reason)`. On a match,
  `reason` is one of the two existing category strings ("Dismissive language about
  educational background" or "Demographic assumptions detected").
- **What changes:** behavior only — more phrasings now map to `True` with a non-empty
  reason. No signature, API, or return-shape change; callers of `detect_bias()` are
  unaffected.

### Risks & unknowns
- **Precision regression (primary risk).** Broadening the regexes risks flagging the
  positive/neutral cases in `tests/unit/test_bias_detector.py` (e.g.
  `test_positive_bootcamp_mention_not_flagged`: "your bootcamp background shows strong
  fundamentals"). Mitigation: re-run the whole test file, not just the 9, after each change.
- **Catastrophic backtracking / readability.** The existing demographic pattern uses `.*`
  (`safety/bias_detector.py:24`); adding more alternation could hurt readability or cause
  slow matching. Mitigation: keep alternations bounded, avoid unbounded `.*` where possible.
- **Unknown — approach preference.** Whether maintainers would prefer a more semantic
  (non-regex) detector. Staying with regex to satisfy the specified unit tests; will note
  this in the PR if relevant.

### Edge cases
The fix must handle these gracefully:

1. **Positive/neutral bootcamp mentions stay unflagged** — "your bootcamp background shows
   strong fundamentals"; "this bootcamp project demonstrates good coding practices".
2. **Observation vs. assumption** — "your resume shows bootcamp attendance" (factual → not
   flagged) vs. "bootcamp attendance means inadequate training" (biased → flagged).
3. **Case-insensitivity** — "BOOTCAMP GRADUATES LACK FUNDAMENTALS" → flagged.
4. **Empty / whitespace-only input** — `""` and `"   \n\t  "` → `(False, '')`.
5. **Singular vs. plural subjects** — developer/developers, graduate/graduates,
   programmer/programmers all detected.
6. **Multiple bias indicators in one sentence** — "young bootcamp graduates can't write
   code and immigrant developers lack fundamentals" → flagged.
