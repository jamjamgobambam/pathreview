## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has text: None
#153, https://github.com/ascherj/pathreview/issues/153]

### Understand

The root cause of this issue is `"text": None` being passed to the
FaithfullnessChecker raising a TypeError

### Map

File: `rag/evaluator/faithfulness_checker.py`

Function: `check()`

Lines: 34:36

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

### Plan

So the steps to fix this were to locate which part of the code was raising the
TypeError. Understand why the error was being raised, the join function is
crashing because it expects a string not None. We will add `or ""` after the
.get method so when the .get method fails, we will have a fallback to an empty
string. Then we will test if this fixes the TypeError being raised and the
FaithfullnessChecker gives the correct output to the None context.

### Inputs & outputs

The fix takes no input and this should allow the FaithfullnessChecker to run the
None input and produce the correct output.

### Risks & unknowns

What I am a little unsure about is the intended behavior, my initial approach
was to check if None was in the 'text' object and return a 0.0 score based on
that, but this approach seems more in line with what the Faithfullness checker
should do which is test the given input which in this case is empty text.

### Edge cases

The inputs that this fix should handle now is the `"text": None` not raising a
TypeError
