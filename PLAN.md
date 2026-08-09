# Solution plan

**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation #34
**Issue Link:** https://github.com/ascherj/pathreview/issues/34

## Understand
Currently, `HybridRetriever` in `rag/retriever/hybrid.py` ranks candidate chunks purely by combining vector similarity and keyword matching scores. However, high vector similarity or keyword matches don't always mean a chunk is actually relevant to the query, leading to noisy context being passed to the generator. Adding an optional LLM re-ranking step will evaluate each retrieved chunk's relevance to the prompt, filtering out noise and passing only the top-k most relevant chunks to the generator.

## Design Decisions: Candidate Strategy, Fallbacks & Over/Under-Fetching

### 1. Over-fetching vs. Under-fetching Trade-off
- **Under-fetching Risk**: If 1st-stage (vector + keyword) retrieval fetches too few candidates (e.g., only 3 chunks), highly relevant chunks might be missed before the LLM Re-ranker even sees them.
- **Over-fetching Risk**: If 1st-stage retrieval fetches too many candidates (e.g., 50 chunks), LLM re-ranking becomes slow and expensive, consuming excessive prompt tokens.
- **Optimal Balance**: Implement 2-stage retrieval — 1st-stage over-fetches a moderate candidate pool (`max_chunks * 2`), and 2-stage LLM Re-ranker prunes and ranks down to exact `max_chunks`.

### 2. When & How Re-ranker is Used
- **When Enabled**: Activated for high-precision generation tasks (e.g., generating final portfolio review reports) or when candidate search space needs fine-grained relevance filtering.
- **When Bypassed**: Bypassed when `reranker=None` (e.g., offline unit tests, fast keyword lookups, or when LLM API keys are unconfigured).

### 3. Graceful Fallback Strategy
- **Fallback Plan**: If the LLM re-ranking API times out, rate-limits, or returns unparseable output, `HybridRetriever` logs a warning and automatically falls back to standard vector + keyword blended scores without throwing an unhandled exception.

## Map
- `rag/retriever/reranker.py` (new): Implements `LLMReranker` to score chunk relevance using a lightweight LLM prompt.
- `rag/retriever/hybrid.py` (modify): Accepts an optional `reranker` instance and executes the re-ranking pass on blended candidates.
- `tests/unit/test_reranker.py` (new): Unit tests for LLM re-ranking scoring, sorting, and fallback logic.

## Plan & Subtasks Timeline (Total: 7–10 Hours)
- **Subtask 1: Observe Baseline & Identify Noisy Chunks** *(1–2 hours)*
  Test current `HybridRetriever` on sample queries, document cases where off-topic chunks receive high similarity scores, and establish baseline output.
- **Subtask 2: Implement `LLMReranker`** *(2–3 hours)*
  Create `rag/retriever/reranker.py` with a structured prompt that scores chunk relevance (0–1 scale) for a given query, including JSON score parsing.
- **Subtask 3: Integrate into `HybridRetriever`** *(2 hours)*
  Update `retrieve()` in `hybrid.py` to accept an optional `reranker: LLMReranker | None = None` and execute 2nd-stage candidate pruning.
- **Subtask 4: Compare Before vs. After** *(1–2 hours)*
  Run comparison tests evaluating retrieval accuracy with and without the LLM re-ranker pass to measure noise reduction and precision improvement.
- **Subtask 5: Add Unit Tests** *(1–2 hours)*
  Write comprehensive unit tests in `tests/unit/test_reranker.py` covering score parsing, error fallbacks, empty inputs, and threshold filtering.

## Inputs & outputs
- **Inputs**: User query string, candidate text chunks (dicts with content and metadata), target `max_chunks` count.
- **Outputs**: Re-ranked and filtered list of the top-k most relevant text chunks sorted by LLM relevance score.

## Risks & unknowns
- **Latency & Cost**: Calling the LLM for every chunk can introduce latency. *Mitigation*: Batch candidates into a single prompt call or limit candidate re-ranking depth.
- **Parsing Failures**: LLM may return unexpected format. *Mitigation*: Include robust JSON parsing and fall back to hybrid scores if parsing fails.

## Edge cases
- Empty chunk list returned by initial vector/keyword search.
- LLM API timeout or error during re-ranking (fallback to original hybrid ranking).
- Candidate count is smaller than requested `max_chunks`.
