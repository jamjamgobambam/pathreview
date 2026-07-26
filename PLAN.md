## Solution plan

**Issue:** [Hybrid retriever over-weights keyword results when query contains technology names #24](https://github.com/ascherj/pathreview/issues/24)

### Understand
The root cause of this issue is the schematic chunking. The data is getting retrived but the chunks are not being evaluated properly to get relevant results. This causes sometimes unexpected behaviors that seem relevant.

### Map
I expect to touch `rag/retriver/hybrid.py` and `app.py`.

### Plan
1. Retry the prompt to see if that could fix the problem.
2. Review the code in `hybrid.py` to decide where the root of the problem might be.
3. Trace through the code and look at other files in `rag/retriver`.
4. Fix the problem by reframing how chunks are sorted. 

### Inputs & outputs
The fix takes in the query from the user and the profile id to know which user the question is referring to. It returns all of the chunks in a list.

### Risks & unknowns
What could go wrong is the evaluation of the individual chunks that are being sent for NLP. What is unknown currently is how the chunks are being retreived.

### Edge cases
The fix should gracefully handle a situation where there are no chunks to be retrieved.