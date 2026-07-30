# PLAN: Fix faithfulness checker short claim support

## Problem

Short factual claims like "The candidate knows Python." are currently mis-scored as unsupported in the faithfulness checker. The existing `_is_supported()` heuristic requires at least 2 meaningful overlapping tokens, which fails with short claims that contain only a single strong keyword.

## Goal

Ensure short factual claims and compound feedback segments can be correctly marked as supported when the context contains the matching core term.

## Scope

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`
- `JOURNAL.md`

## Proposed solution

1. Improve claim extraction
   - Keep sentence splitting, but also split compound claims by commas and conjunctions such as "and"/"or".
   - Preserve short factual segments for scoring rather than discarding them because of length.

2. Update support heuristic
   - Use regex tokenization instead of simple `.split()`.
   - Remove stop words and generic claim terms from the claim and context.
   - Allow a short claim with one strong matching token to be considered supported.
   - Retain the existing two-token overlap requirement for longer claim cores.

3. Add reproduction evidence
   - Add a regression test for the exact short claim issue.
   - Add `JOURNAL.md` notes documenting the reproduction steps and observations.

4. Validate
   - Run targeted unit tests for faithfulness.
   - Verify the modified file compiles.

## Risks / unknowns

- The heuristic could become too permissive for some generic short claims; generic terms must be filtered properly.
- Compound claim splitting may over-segment some natural sentences, but the tradeoff is better support detection for enumerated skill lists.

## Files touched

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`
- `JOURNAL.md`
- `PLAN.md`
