Solution plan

Issue: Faithfulness checker crashes when a context chunk has text: None — https://github.com/ascherj/pathreview/issues/153

Understand
chunk.get("text", "") only applies the default "" when the "text" key is missing from the dict entirely. If the key exists but its value is explicitly None (e.g. a chunk from ingestion that failed to extract text), .get() returns None as-is. The following " ".join([...]) call then raises TypeError: sequence item 0: expected str instance, NoneType found, since str.join() requires every element to be a string.

Expected behavior: a chunk with text: None should be treated like one with missing or empty text, contribute nothing to the joined context, and let scoring continue normally, returning a float between 0.0 and 1.0.

Actual behavior: any context_chunks list containing {"text": None} crashes check() entirely with an unhandled TypeError.

Map
rag/evaluator/faithfulness_checker.py, the check() method, specifically the context_text = " ".join([...]) line (already flagged with a BUG (#153) comment from the Week 8 reproduction commit)
tests/unit/test_faithfulness_checker.py, no new file needed; test_none_context_chunk_text already exists and currently fails; it becomes the regression test once the fix lands. Will add one more edge-case test for mixed chunks.
_extract_claims() and _is_supported() are not touched, they operate on already-flattened strings, not raw chunk dicts.

Plan

Change chunk.get("text", "") to chunk.get("text") or "" so both a missing key and an explicit None value normalize to an empty string.
Run test_none_context_chunk_text and confirm it passes.
Run the full test_faithfulness_checker.py file to confirm no regressions, especially test_missing_text_key_in_chunk, which already passes.
Add a new test for a mixed chunk list (some text: None, some valid text) to confirm partial None values don't crash or skew scoring.
Grep the codebase for the same chunk.get("text", "") pattern elsewhere (ingestion/retrieval code) to check if the same bug exists there; note in the PR description even if out of scope for this fix.

Inputs and outputs
Input: context_chunks, a list of dicts where "text" may be a string, None, or missing. Output: context_text, a joined string that never raises, treating missing and None values as empty. check() continues returning a float between 0.0 and 1.0 for this input shape.

Risks and unknowns
Unknown whether the same .get("text", "") gap exists elsewhere in ingestion/retrieval, if so, this may be a symptom of a wider pattern.
PR#162 is already open against this issue; need to check it before opening my own PR to avoid duplicating or conflicting work.
Uncertain whether normalizing (or "") vs filtering out None-text chunks entirely is the intended fix, filtering could silently drop chunks callers expect to count. Defaulting to normalizing since it's the smaller, safer change.

Edge cases
Missing "text" key (already handled, test_missing_text_key_in_chunk)
"text": None (the bug itself, test_none_context_chunk_text)
"text": "" (already works)
Mixed list with some None, some valid text (new test to add)
Empty context_chunks list (already handled by the early return guard)
