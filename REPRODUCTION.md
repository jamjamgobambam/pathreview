# Reproduction — Issue #153

## Command
.venv/Scripts/python -m pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v

## Result
The existing test test_none_context_chunk_text fails with:

TypeError: sequence item 0: expected str instance, NoneType found
rag\evaluator\faithfulness_checker.py:34: TypeError

## Root cause confirmed
In FaithfulnessChecker.check() (rag/evaluator/faithfulness_checker.py, line 34), the code does:

context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])

dict.get("text", "") only returns the default "" when the key "text" is missing entirely.
When the key exists but its value is None (e.g. {"text": None}), .get() returns None,
which then breaks " ".join(...) since it requires all items to be strings.

This confirms the bug described in issue #153 is real and reproducible in this environment.
