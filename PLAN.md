## Solution plan

**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation (#34)

### Understand
**What is the root cause of this issue? What behavior is expected vs. actual?**
The current RAG pipeline only uses vector similarity and keyword (BM25) search to rank documents. The expected behavior is to have a final step that uses an LLM to "re-rank" the blended results to ensure they actually answer the user's query before sending them to the generator.

### Map
**Which files, functions, or modules are involved?**
- `rag/retriever/hybrid.py`: Specifically the `retrieve` method. This is where the results are blended and returned.
- A new utility function might be needed for the LLM call to keep the code clean.

### Plan
**What are the steps to fix this issue?**
1. Create a utility function to call the LLM with a scoring prompt (e.g., "Score this chunk from 1-10 on relevance to the query").
2. Update `HybridRetriever.__init__` to optionally accept a flag to enable the LLM re-ranker.
3. Intercept `final_results` in `hybrid.py` right before they are returned.
4. Pass the chunks to the LLM to get a relevance score for each chunk.
5. Re-sort the chunks based on the new LLM score and return them.

### Inputs & outputs
**What does your fix take as input? What should it produce or change?**
- **Input:** The blended results (`final_results`) and the user's original `query`.
- **Output:** A re-sorted list of chunks, prioritized by the LLM score.

### Risks & unknowns
**What could go wrong? What are you still unsure about?**
- **Latency:** Calling an LLM sequentially for 10 chunks will be slow. We may need to score them concurrently or combine them into a single prompt.
- **Parsing:** The LLM might return text (e.g., "Score: 8") instead of a pure integer, so we must safely parse the output.

### Edge cases
**What inputs or states should your fix handle gracefully?**
- If the LLM fails or times out, we should fallback to the original blended scores.
- If the LLM returns an un-parseable score, we should assign a default score so the system doesn't crash.