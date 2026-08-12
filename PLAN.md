## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None` (#153)](https://github.com/ascherj/pathreview/issues/153)

### Understand

`FaithfulnessChecker.check()` builds one context string by joining the value returned
by `chunk.get("text", "")` for every retrieved chunk. The default only applies when
the `text` key is absent; when the key exists and its value is `None`, the generator
passes `None` to `str.join()`, which raises `TypeError` before any claims can be
scored.

Expected behavior: a chunk with missing or `None` text should contribute an empty
string, allowing the checker to continue and return a score between `0.0` and `1.0`.
Actual behavior: `FaithfulnessChecker().check("Knows Python.", [{"text": None}])`
raises `TypeError: sequence item 0: expected str instance, NoneType found`.

### Map

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker.check()` extracts and joins context chunk text.
- `tests/unit/test_faithfulness_checker.py`
  - `test_none_context_chunk_text` is the focused regression test.
  - `test_missing_text_key_in_chunk` protects the related missing-key case.

No API route, database model, migration, frontend component, or LLM integration is
involved in this fix.

### Plan

1. Reproduce issue #153 with a context list containing `{"text": None}` and confirm
   the failure occurs while `check()` constructs `context_text`.
2. Normalize each retrieved `text` value in
   `rag/evaluator/faithfulness_checker.py` so both a missing key and an explicit
   `None` become an empty string before `str.join()` runs.
3. Run `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` to verify
   both nullable-input paths return a valid numeric score without an exception.
4. Run the complete faithfulness-checker test module and the repository quality
   checks, separating any pre-existing failures from regressions caused by this
   focused change.

### Inputs & outputs

The input is generated feedback as a string and retrieved context as a
`list[dict]`. Each dictionary may have a string `text` value, a missing `text` key,
or `text: None`.

The fix does not change the public method signature or return type. For valid
feedback and a non-empty chunk list, `check()` should continue to produce a
faithfulness score from `0.0` to `1.0`; null or missing chunk text simply contributes
no supporting words.

### Risks & unknowns

- Using a broad truthiness fallback would also normalize other falsey values such
  as `0` or `False`. Retrieved chunk text is typed and produced as text in normal
  operation, but an explicit `None` check could be preferable if non-string values
  become supported later.
- Normalizing invalid text prevents the crash but can lower the score because that
  chunk supplies no evidence. This is preferable to inventing context, but upstream
  retrieval or ingestion may still need separate validation if null text becomes
  common.
- The full `tests/unit/test_faithfulness_checker.py` module currently contains
  unrelated scoring-expectation failures. The issue-specific regression test must
  pass independently, and those baseline failures should not be hidden or expanded
  into issue #153.

### Edge cases

- A single chunk with `text: None`.
- A chunk with no `text` key.
- A mixture of valid text, missing text, and `None` text across several chunks.
- All chunks containing unusable text, which should yield a valid low score rather
  than an exception.
- Empty feedback or an empty context list, which should retain the existing `0.0`
  early-return behavior.
