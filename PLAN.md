# Issue #38 Solution Plan

## Solution plan

**Issue:** [Add an integration test that runs the full RAG pipeline against a mock LLM](https://github.com/ascherj/pathreview/issues/38)

### Understand

PathReview has unit tests for individual RAG components, but it does not currently have an integration test that verifies the components work together as one complete workflow. The missing test should run a representative query through retrieval, result ordering or reranking, LLM generation, and response parsing.

The expected behavior is for the full RAG pipeline to return predictable structured feedback while using a mock LLM provider. The test must not contact a real external LLM service or require a real API key.

The actual behavior is that `tests/integration/test_rag_pipeline.py` does not exist. The `tests/integration` directory currently contains only `__init__.py`, so pytest cannot collect a complete RAG pipeline integration test.

### Map

The primary file I expect to create is:

* `tests/integration/test_rag_pipeline.py` — new integration test for the complete RAG workflow.

The following files and modules are likely involved:

* `rag/retriever/hybrid.py` — combines vector and keyword retrieval results and orders them.
* `rag/retriever/vector_store.py` — stores and retrieves document chunks using vector similarity.
* `rag/retriever/keyword_search.py` — indexes chunks and performs keyword retrieval.
* `rag/evaluator/relevance_scorer.py` — calculates how relevant retrieved content is to the query.
* `rag/generator/review_generator.py` — builds the prompt, calls the LLM client, and sends the response to the parser.
* `rag/generator/output_parser.py` — converts the generated response into structured feedback.
* `tests/conftest.py` — may contain reusable pytest fixtures.
* `tests/unit/test_keyword_search.py` — examples for indexing and retrieving deterministic test documents.
* `tests/unit/test_relevance_scorer.py` — examples for relevance-score assertions.
* `tests/unit/test_output_parser.py` — examples of valid mock LLM output and parser assertions.
* `tests/unit/test_llm_provider_contract.py` — should be inspected for existing mock LLM patterns.

I do not currently expect to change production code. I will first attempt to implement the integration test using existing public interfaces, pytest fixtures, and mocking.

### Plan

1. **Trace the RAG component interfaces.**
   Read the constructors and public methods in the retriever, scorer, generator, and parser modules. Determine the exact input and output types passed between retrieval, reranking, generation, and parsing.

2. **Locate the existing mock LLM pattern.**
   Search the test suite and provider modules for the mock LLM provider mentioned in issue #38. Determine whether the integration test should instantiate an existing mock provider or patch the OpenAI-compatible client used by `ReviewGenerator`.

3. **Create deterministic test data.**
   Define a representative query and several document chunks, including at least one relevant chunk and one irrelevant chunk. Give the chunks stable identifiers and metadata so the expected retrieval order is predictable.

4. **Configure isolated retrieval components.**
   Use a temporary vector-store directory and a unique collection name so the test does not depend on or modify local development data. Index the deterministic chunks in both the vector and keyword retrieval components.

5. **Run retrieval and reranking.**
   Send the query through the retrieval pipeline and confirm that the relevant chunk is returned and ranked above the irrelevant chunk. Verify that the retrieved result contains the fields required by the generation stage.

6. **Mock the LLM response.**
   Configure the mock LLM to return fixed, valid structured review output. Assert that no real network request is made and that the prompt passed to the mock contains content from the retrieved chunk.

7. **Verify generation and parsing.**
   Run the generation and parsing stages and assert that the final structured result contains the expected feedback section, summary, strengths, improvements, evidence, and score.

8. **Run the tests and check regressions.**
   Run the new integration test by itself, followed by the relevant RAG unit tests. Confirm that the test is deterministic and does not require an API key, internet connection, or existing database state.

### Inputs & outputs

#### Inputs

The integration test will use:

* A representative user query.
* A small collection of deterministic document chunks.
* At least one relevant and one irrelevant chunk.
* Stable chunk identifiers and metadata.
* Mock or deterministic embeddings.
* A temporary vector-store location.
* A unique test collection name.
* Any profile or configuration object required by `ReviewGenerator`.
* A fixed mock LLM response containing valid structured JSON.

#### Outputs

The retrieval stage should produce a nonempty ordered list of results containing document text, metadata, and scores.

The reranking or score-ordering stage should place the most relevant chunk ahead of unrelated chunks.

The generation stage should receive a prompt containing the retrieved context and return the fixed mock response.

The parsing stage should produce structured feedback objects with specific expected values.

The completed integration test should pass locally and in CI without:

* A real LLM API key.
* An external network request.
* Pre-existing vector-store data.
* Manual application startup.

### Risks & unknowns

* **Meaning of reranking:** `rag/retriever/hybrid.py` appears to combine vector and keyword scores, while `rag/evaluator/relevance_scorer.py` performs separate relevance scoring. I need to determine whether issue #38 expects one or both of these operations in the test.

* **Mock LLM location:** The issue refers to a mock LLM provider, but I still need to identify its exact implementation. I will search the provider modules and `tests/unit/test_llm_provider_contract.py` before creating a new mock.

* **Generator client interface:** `rag/generator/review_generator.py` may expect an OpenAI-compatible response object with nested choices and message content. The mock must match the exact attributes accessed by the generator.

* **Persistent vector-store state:** `rag/retriever/vector_store.py` may use persistent ChromaDB storage. Using the default development collection could make the test depend on previous runs, so the test should use pytest's `tmp_path` fixture and a unique collection.

* **Keyword index setup:** `KeywordSearcher` must be indexed before searching. An empty index currently raises an error in an existing unit test, so the integration test must populate the index with valid chunks before executing the query.

* **Existing unrelated failures:** Some current unit tests fail for reasons outside issue #38. I must avoid changing those components unless a change is required specifically for the new integration test.

* **Production orchestration:** I need to determine whether an existing service function already connects the complete RAG pipeline. If no orchestration entry point exists, the integration test may need to assemble the existing components directly.

### Edge cases

* The query retrieves no documents because all results are below the minimum score. The pipeline should handle an empty context predictably and should not make an uncontrolled external request.

* Vector and keyword retrieval return tied or nearly tied scores. The test should avoid brittle assertions unless the implementation defines a deterministic tie-breaking rule.

* The mock LLM returns valid JSON wrapped in a Markdown code fence. The parser should still produce structured feedback.

* The mock LLM returns malformed JSON. The parser should follow its documented fallback behavior rather than crashing unexpectedly.

* A retrieved chunk is missing optional metadata. Prompt construction should either handle the missing field gracefully or produce a clear expected error.

* The vector store contains stale information from an earlier test. Using an isolated temporary directory and unique collection should prevent cross-test contamination.

* The mock is applied incorrectly and the generator attempts a real network request. The test should patch or inject the mock before generation and must not depend on an API key.

* Retrieval returns the correct document but in a different score order because of floating-point differences. Assertions should focus on meaningful ranking and content rather than unnecessary exact score equality.
