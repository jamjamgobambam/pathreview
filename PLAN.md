## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None - https://github.com/ascherj/pathreview/issues/153

### Understand
The root cause is in FaithfulnessChecker.check(). It builds context_text using chunk.get("text", "") for each chunk. .get()'s default only applies when the key is missing, not when the key exists with value None. So when a chunk is {"text": None}, .get() returns None, and " ".join([...]) then raises TypeError: sequence item 0: expected str instance, NoneType found because join() requires all items to be strings. Expected behavior: the checker should treat a chunk with text: None the same as an empty/missing chunk (contribute an empty string to the context) and return a valid float score, not crash.

### Map
- rag/evaluator/faithfulness_checker.py - contains the buggy line (check() method, around line 34)
- tests/unit/test_faithfulness_checker.py - contains test_none_context_chunk_text, the test that currently fails and defines expected behavior
- No other files are expected to need changes; the fix is isolated to how each chunk's text is extracted

### Plan
1. In check(), replace chunk.get("text", "") with logic that explicitly handles None values, e.g. chunk.get("text") or ""
2. Run test_none_context_chunk_text locally to confirm it now passes
3. Run the full test file (pytest tests/unit/test_faithfulness_checker.py) to confirm no other tests regressed
4. Manually verify the exact repro command from REPRODUCTION.md no longer raises TypeError
5. Review the fix against CONTRIBUTING.md code style (docstrings, Google style) before opening the PR

### Inputs & outputs
- Input: context_chunks: list[dict], where each dict may have a "text" key that is a string, None, or missing entirely
- Output (unchanged): check() still returns a float between 0.0 and 1.0
- Behavior change: chunks with text: None (or missing "text") now contribute an empty string to context_text instead of crashing

### Risks & unknowns
- Risk: using chunk.get("text") or "" would also silently convert falsy-but-valid values (an empty string is fine, but if text were ever 0 or False due to a data bug elsewhere, this pattern would mask that) - need to confirm text is only ever expected to be str | None in this codebase
- Unknown: whether other chunk fields (e.g., a metadata dict) have the same None-handling issue elsewhere in rag/evaluator/ - worth a quick search with grep -rn ".get(\"text\"" rag/ to check for similar patterns
- Risk: need to confirm the fix doesn't change scores for any of the other passing tests in test_faithfulness_checker.py, since many of them rely on exact score thresholds

### Edge cases
1. A single chunk with {"text": None} - must not crash, should produce a valid float
2. Multiple chunks where some have None and others have valid text (e.g., [{"text": None}, {"text": "Python"}]) - should still concatenate the valid text correctly
3. A chunk missing the "text" key entirely (already covered by test_missing_text_key_in_chunk) - must continue to work exactly as before
4. All chunks having text: None - should behave like an empty context, not crash
