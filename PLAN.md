## Solution plan

**Issue:** [Add an integration test that runs the full RAG pipeline against a mock LLM (#38)](https://github.com/ascherj/pathreview/issues/38)

### Understand

PathReview has unit tests for individual retrieval, generation, and parsing
components, but `tests/integration` contains no test module. Running
`pytest --collect-only -q tests/integration` therefore reports that no tests
were collected. As a result, the repository does not verify the contracts
between `HybridRetriever.retrieve`, `ReviewGenerator.generate_full_review`,
and `parse_review_output` in one complete query flow.

The expected behavior is a deterministic, offline integration test that starts
with a query and profile data, retrieves and ranks relevant chunks, passes
those chunks into review generation, returns a fixed mock LLM response, and
asserts that the response becomes structured `FeedbackSection` objects.
Currently, those components are only exercised separately. There is also no
standalone reranker module: `rag/retriever/hybrid.py` performs the relevant
score normalization, blending, sorting, and truncation. There is a
`MockEmbeddingProvider`, but `ReviewGenerator` constructs an OpenAI client
directly, so the test must replace the client's completion call at the network
boundary.

### Map

Files and code involved:

- `tests/integration/test_rag_pipeline.py` — new integration test, deterministic
  fixtures/fakes, end-to-end invocation, and assertions.
- `tests/conftest.py` — only if profile, chunk, or fake-response fixtures are
  useful outside this one test; otherwise fixtures will stay local to the new
  integration test.
- `rag/retriever/hybrid.py` — `HybridRetriever.retrieve` combines vector and
  BM25 results, normalizes scores, and orders the final context.
- `rag/retriever/keyword_search.py` — `KeywordSearcher.index` and `search`
  provide the keyword half of hybrid retrieval.
- `rag/retriever/vector_store.py` — defines the vector-store contract that the
  test fake must satisfy without writing to persistent ChromaDB storage.
- `rag/generator/review_generator.py` — `ReviewGenerator.generate_full_review`
  formats retrieved context, calls the OpenAI-compatible client, parses the
  response, and adds citations.
- `rag/generator/output_parser.py` — `parse_review_output` converts the fixed
  JSON response into `FeedbackSection` instances.

The intended production-code footprint is zero. If the test reveals that the
OpenAI client cannot be replaced cleanly, a small dependency-injection change
to `rag/generator/review_generator.py` will be considered and documented
before expanding scope.

### Plan

1. Add local deterministic fixtures to
   `tests/integration/test_rag_pipeline.py`: profile data, candidate chunks, a
   fake vector-store collection/query result, and an OpenAI-shaped chat
   completion response. Keep all storage in memory and make no network calls.
2. Index the same candidate chunks with `KeywordSearcher`, construct
   `HybridRetriever`, embed the query with `MockEmbeddingProvider`, and call
   `retrieve`. Assert that results are non-empty, sorted by blended score,
   limited to the requested count, and include the expected relevant source.
3. Construct `ReviewGenerator`, replace its client's
   `chat.completions.create` boundary with the deterministic fake, and pass the
   retrieved chunks to `generate_full_review`. This connects retrieval/ranking
   to prompt generation and parsing rather than retesting either component in
   isolation.
4. Assert the final `FeedbackSection` values, source citations, section count,
   and mock call arguments. Also assert that the prompt includes text from the
   retrieved context and that no real API call or persistent ChromaDB directory
   is used.
5. Run the focused integration test, then the repository test suite and lint
   checks. Record any unrelated environment failures separately so they are
   not confused with failures in the new pipeline test.

### Inputs & outputs

The test takes a plain-text review query, its deterministic mock embedding, a
profile identifier and profile metadata, and an in-memory set of chunks with
IDs, text, metadata, and vector scores. The fake LLM returns a fixed
OpenAI-compatible response containing valid JSON feedback.

The retrieval output should be an ordered list of chunk dictionaries with
normalized vector and keyword scores plus a blended `score`. The generation
output should be a list of `FeedbackSection` objects with predictable section
names, content, confidence values, suggestions, and citations derived from the
retrieved chunk metadata. The test itself should pass without credentials,
network access, Docker services, or persistent data.

### Risks & unknowns

- The issue says “reranking,” but there is no reranker class. The current
  investigation treats the blending and sorting in
  `HybridRetriever.retrieve` as reranking; maintainer feedback could call for a
  different intended path.
- `HybridRetriever._get_all_chunks` fetches chunks but does not index them into
  `KeywordSearcher`. The test must explicitly call `KeywordSearcher.index`;
  otherwise it would accidentally cover only vector retrieval.
- The production `VectorStore` uses persistent ChromaDB and its query result
  shape is nested. A simplistic fake could pass while violating the real
  contract, so the fake will mirror the methods and dictionary fields consumed
  by `HybridRetriever`.
- `ReviewGenerator.generate_full_review` makes five LLM calls and catches
  per-section exceptions. The fake must provide enough responses and the test
  must assert calls so an internal error cannot be hidden by fallback error
  sections.
- `parse_review_output` uses JSON object keys as section names, which may not
  match the requested prompt section. The mock response and assertions must
  make that behavior explicit rather than assuming the parser renames output.
- The current shell environment is missing project dependencies such as
  `structlog` and `rank_bm25`, so the full unit suite cannot collect until the
  development dependencies are installed. The focused test must be verified in
  the project-supported environment before completion.

### Edge cases

- Vector search or keyword search returns no candidates, or only one retriever
  finds a chunk.
- All vector or BM25 scores are zero, avoiding division-by-zero during score
  normalization.
- Duplicate chunk IDs appear in both retrieval methods and must merge into one
  ranked result.
- More candidates match than `max_chunks`, and candidates below `min_score`
  must be excluded.
- Retrieved chunks omit optional metadata such as `source_id`; context
  formatting and citation logic should still succeed.
- The mock LLM returns fenced JSON, raw JSON, or malformed/plain text; the
  parser should produce a usable `FeedbackSection` through its documented
  fallback.
- Empty retrieved context or an LLM exception should not trigger a real
  network call and should produce the generator's defined fallback behavior.
