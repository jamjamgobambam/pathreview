## Solution plan

**Issue:** [Add an integration test that runs the full RAG pipeline against a mock LLM #38](https://github.com/ascherj/pathreview/issues/38)

### Understand
The RAG pipeline has three stages: retrieval (`HybridRetriever`), generation (`ReviewGenerator`), and evaluation (`EvalSuite`). Each stage has unit tests in `tests/unit/`, but no test exercises all three together. The expected behavior is that given a profile and a query, the pipeline retrieves relevant chunks, passes them to the generator, and the evaluator scores the output — all without hitting a real LLM or ChromaDB instance. The gap means regressions at the boundaries between stages (e.g. wrong chunk format passed to generator) would go undetected.

### Map
Files involved:

- `tests/integration/test_rag_pipeline.py` — new file, the integration test lives here
- `rag/retriever/hybrid.py` — `HybridRetriever.retrieve()` is the entry point
- `rag/retriever/vector_store.py` — `VectorStore` needs to be mocked (uses ChromaDB)
- `rag/retriever/keyword_search.py` — `KeywordSearcher` needs a pre-built index
- `rag/generator/review_generator.py` — `ReviewGenerator.generate_full_review()` calls the OpenAI client, which must be mocked
- `rag/generator/output_parser.py` — `parse_review_output()` is called internally; mock LLM response must produce parseable output
- `rag/evaluator/eval_suite.py` — `EvalSuite.run()` is the final stage; scores the output
- `tests/conftest.py` — shared fixtures (may add pipeline-level fixtures here)

### Plan
1. Set up mock dependencies — use `unittest.mock.MagicMock` to mock `VectorStore` (so no ChromaDB needed) and patch `openai.OpenAI` so the generator returns a controlled JSON response without a real API call.
2. Build a minimal in-memory pipeline — instantiate `KeywordSearcher`, index a small set of fixture chunks, then wire it with the mocked `VectorStore` into `HybridRetriever`.
3. Run retrieval and assert output shape — call `HybridRetriever.retrieve()` with a test query and a fake embedding, assert the returned list contains dicts with `text`, `score`, and `metadata` keys.
4. Run generation and assert output shape — pass the retrieved chunks and a sample `profile_data` dict to `ReviewGenerator.generate_full_review()`, assert it returns a non-empty list of `FeedbackSection` objects with non-empty `content`.
5. Run evaluation and assert scores are in range — pass the query, chunks, and generated feedback to `EvalSuite.run()`, assert `relevance_score`, `faithfulness_score`, and `overall_score` are all between 0.0 and 1.0.

### Inputs & outputs
- Input: a small list of fixture chunks (plain dicts with `id`, `text`, `metadata`), a fake 3-dimensional query embedding, a sample `profile_data` dict, and a mock LLM response string in the JSON format `output_parser.py` expects.
- Output: the test passes when all three pipeline stages complete without error and the data contracts between stages are satisfied (correct types, non-empty content, scores in valid range).

### Risks & unknowns
- `HybridRetriever._get_all_chunks()` calls `collection.get()` directly on the ChromaDB collection object — the mock for `VectorStore.get_collection()` must return an object that also supports `.get()` with the right return shape, otherwise the keyword indexing step will fail silently.
- `ReviewGenerator` instantiates `openai.OpenAI` in `__init__`, so the patch must be applied before the object is constructed, not after.
- `EvalSuite` internally creates `RelevanceScorer` and `FaithfulnessChecker` — need to check `rag/evaluator/relevance_scorer.py` and `faithfulness_checker.py` to confirm they don't make external calls before deciding whether to mock them too.
- The mock LLM response must be valid JSON matching the structure `_parse_json_output` expects, otherwise the parser falls back to plaintext and section names will differ from what the test asserts.

### Edge cases
- Empty retrieval result (no chunks above `min_score`) — generator should still return sections, each with an error message rather than crashing.
- Mock LLM returns malformed JSON — `parse_review_output` falls back to `_parse_plaintext_output`; the test should handle both paths or explicitly test the fallback separately.
- `profile_data` missing optional keys like `projects` or `github_username` — `generate_section` uses `.get()` with defaults, so this should be safe, but worth asserting.
- Duplicate section names returned by generator — `_consolidate_feedback` deduplicates by `section_name`; verify the final list length matches expectations.
