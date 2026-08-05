## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has text: None #153](https://github.com/ascherj/pathreview/issues/153)

### Understand
The root cause is in the check() method of the faithfulness checker. It uses chunk.get("text", "") to extract text from context chunks. While .get() handles missing keys by returning the default "", it does not replace an explicit None value. When "".join() is called later on a list containing None, Python raises a TypeError.

### Map
- **Files involved:** rag/evaluator/faithfulness_checker.py
- **Tests involved:** tests/unit/test_faithfulness_checker.py

### Plan
1.  **Isolate the failing logic:** Locate the list comprehension or loop in rag/evaluator/faithfulness_checker.py that extracts "text" from chunks.
2.  **Add a null-check:** Update the extraction logic to ensure that if a value is None, it is converted to an empty string "" before being added to the context list.
3.  **Verify with existing tests:** Run pytest to ensure test_none_context_chunk_text now passes.
4.  **Regression testing:** Run the full suite for the RAG module to ensure no other evaluation logic was broken.

### Inputs & outputs
- **Input:** A list of context chunks where one or more chunks have {"text": None}.
- **Output:** A successfully joined context string that treats None as "", allowing the faithfulness check to proceed to the LLM evaluation stage.

### Risks & unknowns
- **Risk:** If the LLM receives an empty context because all chunks were None, the evaluation might be technically "successful" but practically useless. I need to ensure the fix doesn't mask deeper data ingestion issues.
- **Unknown:** I need to check if other checkers (e.g., Answer Relevancy) share this same vulnerable pattern.

### Edge cases
- **All chunks are None:** The system should return a neutral or "unable to evaluate" result rather than crashing.
- **Missing "text" key vs. None value:** The fix must handle both scenarios gracefully.
