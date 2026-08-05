# PLAN.md — Issue #151: Bias detector patterns are too narrow to match common phrasings

## What needs to change

The bug is in `BiasDetector.detect_bias()` in `safety/bias_detector.py`. The
regex patterns it uses are over-anchored to exact phrasings — specific verbs
("is", "lack/missing", "doesn't prepare"), specific nouns in the singular only
("developer" instead of "developers"), and specific connective phrases
("person from", "coming from"). Real dismissive/biased feedback that expresses
the same underlying bias with a different verb, plural noun, or sentence
structure slips through undetected.

A correct implementation replaces the narrow, structure-specific regexes with
matching that separates two independent concerns: (1) *is a protected/dismissed
category mentioned* (bootcamp, self-taught, age, immigrant status, income
background, etc.) and (2) *is it framed dismissively/negatively* (can't, lacks,
inadequate, not equal to, means inadequate, etc.), then flags when both are
present in reasonable proximity — rather than requiring one exact fixed
sentence template per case.

## Files / parts of the codebase involved

- `safety/bias_detector.py` — the only file with actual logic to change:
  `BiasDetector.DISMISSIVE_PATTERNS`, `BiasDetector.DEMOGRAPHIC_PATTERNS`,
  and the matching logic inside `detect_bias()`.
- `tests/unit/test_bias_detector.py` — defines the 32 tests (9 currently
  failing) that specify expected behavior; no changes needed here unless a
  new edge case surfaces during implementation that isn't yet covered.
- No other module calls into `BiasDetector` directly in a way that changes
  its public signature (`detect_bias(text: str) -> tuple[bool, str]` stays
  the same) — this is a self-contained fix within the safety layer.

## Root causes traced from the failing tests

| Failing test | Root cause in current regex |
|---|---|
| `test_dismissive_bootcamp_language_detected` | Pattern requires `lack/missing` + `rigor/fundamentals/proper training`; doesn't cover "can't write production code" |
| `test_bootcamp_lacks_rigor_detected` | Pattern requires literal word "is" before insufficient/inadequate/lacks; "education **lacks** fundamentals" has no "is" |
| `test_demographic_assumption_age_detected` | Pattern matches singular "developer" only; "young **developers**" (plural) doesn't match |
| `test_coding_bootcamp_variant` | Pattern requires "doesn't/does not prepare"; text says "can't write enterprise code" |
| `test_developer_vs_programmer_distinction` | Plural-noun issue again, plus "programmers" isn't in the noun list at all |
| `test_multiple_bias_indicators` | Combines two phrasings, neither covered individually |
| `test_negative_educational_claim` | Pattern requires literal "is not/never equal to"; text has "**are** not equal to" |
| `test_rich_poor_assumption` | Pattern requires literal "person from"/"coming from"; text says "developers **from** poor backgrounds" |
| `test_assumption_vs_observation` | "attendance **means** inadequate training" — no pattern covers this construction |

## Sub-tasks

1. **Extract category keyword sets.** Replace the fixed noun lists in the
   regexes with word-boundary-matched keyword groups: `EDUCATION_TERMS`
   (bootcamp, self-taught, online course), `ROLE_TERMS` (developer(s),
   programmer(s), engineer(s)) so any role noun in singular or plural is
   covered, and `DEMOGRAPHIC_TERMS` (age words, immigrant/international/
   foreign, income-background phrases).
2. **Extract dismissive-framing keyword sets.** Build a `NEGATIVE_CAPABILITY`
   group covering the verb phrases that currently only match one exact form:
   can't/cannot/won't, lacks/lack/missing, inadequate/insufficient, not
   equal/comparable to, means inadequate, doesn't/does not prepare.
3. **Rewrite `detect_bias()` matching logic** to check for a category term
   AND a negative-framing term appearing in the same sentence/clause (e.g.
   split on `.`/`;`/` and ` and check both keyword groups against each
   clause) rather than requiring one rigid full-sentence regex per case.
   This directly fixes the plural-noun bug and the "is"-required bug in one
   change instead of patching each regex individually.
4. **Re-run the full test suite** (`pytest tests/unit/test_bias_detector.py -v`)
   after each of the two keyword-group changes above, not just at the end,
   to catch regressions in the 23 currently-passing tests as soon as they
   happen rather than debugging a large diff at once.
5. **Manually test 5–10 adversarial neutral sentences** not in the test
   suite (see edge cases below) to check for new false positives introduced
   by loosening the matching, before opening the PR.
6. **Run `make check`** (lint + format + type check) and fix any issues
   before marking the PR ready, per `CONTRIBUTING.md`.

## Inputs / outputs

- **Input:** unchanged — a single `text: str` (a snippet of AI-generated
  portfolio feedback).
- **Output:** unchanged signature — `tuple[bool, str]` (`is_biased`, `reason`).
  The `reason` string content may become more specific (e.g.
  distinguishing "dismissive educational language" vs "demographic
  assumption" vs "the two combined") but the type contract stays the same
  so no caller elsewhere in `safety/` or `agent/` needs to change.
- **Behavior that changes:** which inputs return `True` — broadened from
  ~9 exact phrasings to keyword-combination matching across ~30+ phrasings
  covered by the test suite.

## Risks and unknowns

- **Risk — false positives on neutral text** (tied to `detect_bias()` in
  `safety/bias_detector.py`): loosening from exact-phrase to keyword-pair
  matching increases the chance of flagging genuinely neutral feedback, e.g.
  "your resume shows bootcamp attendance" (covered by
  `test_positive_bootcamp_mention_not_flagged` /
  `test_assumption_vs_observation`'s observation half). Need to verify the
  clause-splitting logic doesn't accidentally pair an unrelated negative
  word from one clause with a category term from another.
- **Risk — over-broad `NEGATIVE_CAPABILITY` group** flags legitimate
  constructive criticism that happens to contain "lacks" or "inadequate"
  without any demographic/educational framing (e.g. "this project lacks
  test coverage"). Need to confirm the category-term-AND-negative-term
  co-occurrence requirement (not negative-term alone) prevents this —
  should be tested explicitly since it's not in the current test file.
- **Unknown — clause-splitting approach.** Splitting on `.`/`;`/` and ` is a
  simple heuristic; multi-clause sentences with a category term in one
  clause and negative framing in another (but logically unrelated) could
  still misfire. Need to investigate whether a smaller sentence window
  (e.g. same clause only, not full sentence) is precise enough, or whether
  a proximity/distance check between matched terms is needed instead.
- **Unknown — test coverage gaps.** The current 32 tests don't include
  cases combining protected-category terms with clearly positive framing
  in a way that could trip up a broadened negative-term list (e.g. "young
  developers bring fresh energy" — contains "young" + "developers" but is
  positive). Should add a couple of these manually to catch regressions
  the existing suite wouldn't reveal.

## Edge cases the fix must handle gracefully

1. **Positive/neutral mention with a demographic or educational term present**
   — e.g. "young developers bring fresh energy to the team" or "the
   candidate completed a bootcamp and shows strong fundamentals" — must
   NOT be flagged, even though both contain category terms, because no
   negative-framing term is present.
2. **Negative technical feedback with no demographic/educational term**
   — e.g. "this project lacks test coverage" or "the error handling is
   inadequate" — must NOT be flagged; "lacks"/"inadequate" alone shouldn't
   trigger without a category term present (covered conceptually by
   `test_technical_feedback_not_flagged`, but worth an explicit new case
   given the broadened negative-term list).
3. **Category term and negative term in unrelated clauses of a long sentence**
   — e.g. "the candidate is a bootcamp graduate; separately, the codebase
   lacks documentation" — should ideally not be flagged, since the bias
   isn't actually present; this tests whether clause-splitting is granular
   enough.
4. **Case and whitespace variation** — e.g. "YOUNG DEVELOPERS CAN'T..." or
   text with irregular spacing/line breaks — already partially covered by
   `test_case_insensitive_detection`, but should be re-verified after the
   keyword-group rewrite since `re.IGNORECASE` behavior needs to carry over
   correctly into the new matching approach.
