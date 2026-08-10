## Solution plan
***Issue*** Faithfulness checker crashes when a context chunk has: None[https://github.com/ascherj/pathreview/issue/153]

### Understand
***Root cause:** 'chunk.get('text', '')' returns 'None' instead of '""' when the key "text" exists in a context chunk dictionary with a 'None' value.Attempting "".join(...)on a list containing 'None' raise a 'TypeError'.

***Expected Vs Actual:** Expected behavior is to treat "None" values safely as empty string so execution continues without raising an error.
### Map
* 'rag/evaluator/faithfulness_checker.py
*'test/unit/test_faithfulness_checker.py

### Risk and unknowns
* **Low risk:** converting 'None' to "" simply ignore empty context chunks without causing error.

### Edge cases
* `chunk` is `{"text": None}`
* `chunk` is `{}` (missing the key )
* `chunk.get("text")` contains empty whitespace strings or non-string values