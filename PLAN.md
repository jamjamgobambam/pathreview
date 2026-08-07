## Solution plan

**Issue:** [Implement a re-ranking step that uses an LLM to score retrieved chunks before generation - #34](https://github.com/jamjamgobambam/pathreview/issues/34)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
This issue seeks to fill a gap in the implementation. Currently, the application's rag functionally utilizes a hybrid approach of vector similarity and BM25 keyword search to isolate the top-k relevant chunks. Chunks are then fetched as provided by this retriever. This issue requests the addition of a light-weight LLM ranker which will go above this current chunk retrieval layer, organizing top chunks by relevance.

### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
This issue involves the following files:
* `rag/retriever/hybrid.py`
*` rag/retriever/reranker.py` *(to be created)*


### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. Decide LMM for the reranker and set up environment variable (api key, etc.).
2. Implement reranker in a standalone file, defining LLM system prompt and conforming input output to the current chunking process.
3. Incorporate reranker into the current chunking process, making use of import between relevant files.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
* **Input:** The top-k chunks provided by the current hybrid approach retriever. A list of dictionaries each corresponding to a chunk.
* **Output:** A reorganized list of chunks.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
With using an LLM there is some ambiguity on the reasoning behind the top-k chunk order it may produce. This poses a point where things may go wrong. It will rely heavily on my system prompt to successfully produce successfully.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
I will likely want to consider situations in which the input is empty, contains near duplicates, or contains only one chunks as these make reranker either difficult or obsolete.