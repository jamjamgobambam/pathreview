## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

### Understand

`FaithfulnessChecker.check()` builds one context string with
`chunk.get("text", "")` for each retrieved chunk. That default works when the
key is absent, but a present key whose value is `None` returns `None`; passing
it to `" ".join(...)` raises `TypeError`. The actual behavior is a crash,
whereas the expected behavior is a valid faithfulness score between `0.0` and
`1.0`, with a null text chunk treated as having no usable text.

### Map

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker.check()` contains the failing context concatenation.
- `tests/unit/test_faithfulness_checker.py`
  - `test_none_context_chunk_text` reproduces the crash.
  - `test_missing_text_key_in_chunk` covers the related missing-key case.
  - A mixed valid/null context case should verify that usable text is retained.
- `JOURNAL.md`
  - Records the reproduction and implementation-planning work.

### Plan

1. Update `FaithfulnessChecker.check()` to normalize an explicitly null chunk
   text to an empty string before joining, without changing valid strings.
2. Tighten the existing null-text regression test to assert the expected safe
   score rather than only checking its type and range.
3. Add a mixed-context test containing both `None` and valid text to prove the
   valid context still participates in scoring.
4. Run the focused regression test, the complete faithfulness-checker test
   module, and Ruff on the touched Python files.
5. Run the full unit-test suite, review the issue-scoped diff, and commit the
   implementation and tests to the working branch.

### Inputs & outputs

The changed method takes a feedback string and a list of context dictionaries.
Inputs may include a dictionary with a valid string `text`, a missing `text`
key, or `"text": None`. It should return a float from `0.0` to `1.0`; null
text should contribute no tokens, valid text should remain available for
support scoring, and no `TypeError` should be raised.

### Risks & unknowns

- Converting every value with `str()` could hide malformed upstream data, so
  the fix should target `None` instead of accepting arbitrary types silently.
- A null chunk in a mixed list must not cause valid context to be discarded.
- `rag/evaluator/relevance_scorer.py` has a similar access pattern, but changing
  it would expand the scope beyond issue #153 and should be separate follow-up
  work.
- The scoring algorithm's behavior for empty context text should remain
  unchanged; this issue concerns crash prevention, not scoring redesign.

### Edge cases

- A single context chunk with `"text": None`.
- Multiple chunks containing both null and valid text.
- A chunk with no `text` key.
- Multiple null or missing-text chunks.
- Empty feedback or an empty context list, which should keep their existing
  early-return behavior.
- Valid empty strings, which should remain safe and contribute no tokens.
