# Reproduction — Issue 153

**Command run:** pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text -v

**Observed output:**
FAILED tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text
TypeError: sequence item 0: expected str instance, NoneType found
rag/evaluator/faithfulness_checker.py:34: TypeError

**Confirmed location:** `rag/evaluator/faithfulness_checker.py`, line 34, inside
`FaithfulnessChecker.check()`. The line:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

crashes when a chunk dict has `"text": None` explicitly set, because
`dict.get(key, default)` only returns `default` when `key` is *absent* —
if the key exists with value `None`, `.get()` returns `None`, and
`" ".join(...)` can't join a `None` into the list of strings.