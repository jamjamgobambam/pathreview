# Solution plan: faithfulness checker short claims

## Goal

Fix [#152](https://github.com/ascherj/pathreview/issues/152), where supported short
claims such as `Knows Python. Knows SQL.` cannot be marked faithful. Also make
`FaithfulnessChecker.check()` tolerate a chunk whose `text` value is `None`, the
checker-level failure described in
[#153](https://github.com/ascherj/pathreview/issues/153).

## Diagnosis

The checker currently discards sentences of ten characters or fewer and requires two
matching non-stopword tokens for every remaining claim. A reporter-led claim such as
`Knows SQL` has only one fact token after the reporting verb is removed, so applying
the ordinary two-token rule can never support it. Context text is also joined without
validating each value, so `None` raises `TypeError` before scoring.

Several existing tests also require partial evidence to produce a middle score. A
binary supported/unsupported result cannot satisfy that contract for a single claim.

## Scope

- Update `rag/evaluator/faithfulness_checker.py`.
- Reproduce the failures and add focused unit coverage in
  `tests/unit/test_faithfulness_checker.py`.
- Keep retrieval, generation, prompts, APIs, and other evaluators unchanged.
- Treat #153 only at the `FaithfulnessChecker.check()` boundary; do not claim the
  separate `EvalSuite` path is fixed.

## Implementation

1. Tokenize claims and context consistently, removing surrounding punctuation while
   preserving common technical identifiers such as `C++`, `C#`, `.NET`, `Node.js`,
   `Objective-C`, `R&D`, and `I/O`.
2. Preserve the existing first-ten-claims limit and the ordinary two-term support
   threshold.
3. Recognize a narrow short-claim form only after removing a leading reporting verb,
   optionally preceded by a role or pronoun. Bare one-word feedback remains
   unscoreable.
4. Keep role nouns material unless they occur directly before a reporting verb.
5. Return `1.0` for claims meeting the support threshold and proportional lexical
   credit otherwise, then average the per-claim scores.
6. Ignore missing, `None`, and non-string chunk text while retaining valid sibling
   chunks and logging how many malformed chunks were skipped.

## Tests and acceptance criteria

- The exact #152 example scores `1.0`; unrelated short claims score `0.0`.
- Subject-led reporter forms work without making ordinary role nouns optional.
- Context punctuation and no-space sentence boundaries do not hide supported facts or
  split the covered technical identifiers.
- Malformed context values do not raise or hide valid sibling evidence.
- The first-ten-claims limit and ordinary two-term threshold remain intact.
- Focused tests pass with warnings treated as errors and cover every statement and
  branch in the checker.
- Changed Python files pass Ruff and Black; the checker passes strict mypy.
- A same-environment full-unit comparison introduces no failure absent from `main`.

## Known limitation

This is deterministic lexical overlap, not semantic entailment. It cannot reliably
detect negation, contradiction, or entity attribution, and equivalent ideas expressed
with unrelated vocabulary will not match.
