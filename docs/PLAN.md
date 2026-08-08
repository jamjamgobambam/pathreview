## Solution plan

**Issue:** Add an integration test that runs the full RAG pipeline against a mock LLM
https://github.com/ascherj/pathreview/issues/38

### Understand
There are unit tests for each RAG component in isolation (retrieval, reranking,
generation, parsing) but nothing verifies they work correctly *together*. A bug
introduced at a component boundary could pass all unit tests and still break in production.
Expected behavior: a single test that runs a real query through all four stages using
the mock LLM provider (no live API calls) and asserts on the final parsed
result. Actual behavior: `tests/integration/` contains only `__init__.py`.

### Map
- tests/integration/test_rag_pipeline.py — new file, currently just the xfail stub
-  rag/evaluator/ — parsing stage
-  rag/generator/ — generation stage, where the mock LLM gets injected
-  rag/retriever/ — retrieval stage
- `tests/unit/ — reference for existing unit tests for individual components
- `conftest.py` (root) — existing shared fixtures (`sample_resume_text`, `sample_readme_text`) 

### Map
- tests/integration/test_rag_pipeline.py — new file, currently just the xfail stub
- rag/evaluator/ — parsing stage
- rag/generator/ — generation stage, where the mock LLM gets injected
- rag/retriever/ — retrieval stage
- [confirm: where does reranking live? same folder as retriever, or separate?]
- tests/unit/ — reference for existing unit tests for individual components
- tests/conftest.py — multiple unit tests needed realistic input text which 
  are sample_resume_text and sample_readme_text via @pytest.fixture exist. This allows for the author to only write those sample data once and not copy-pasted everywhere.

  defines shared fixtures like sample_resume_text and sample_readme_text via @pytest.fixture. Any test can use them just by naming them as a parameter. I may add a new `tests/integration/conftest.py` for a
  fixture document corpus and/or a reusable mock-LLM fixture, scoped just to
  integration tests rather than the whole repo.

### Plan
1. Read each unit test file to confirm the exact public interface (function
   signatures, expected input/output types) of retriever, reranker, generator, and parser.
2. Locate the mock LLM provider's class/function and confirm how it's
   constructed and how it's injected into the generator (constructor arg,
   dependency override, environment flag, etc.).
3. Read the fixture (in tests/conftest.py or inline) that builds
   a small, realistic document set for the retriever to operate on.
4. Write test_full_rag_pipeline. It needs to test the mock_llm, chaining 
   retrieve → rerank → generate (mock LLM) → parse, asserting on the final parsed output's shape and key content.
5. Delete the current `xfail` stub and replace it with this real test; run
   `pytest tests/integration/ -v` to confirm it passes.

### Inputs & outputs
**Input:** a sample query string plus a small fixture corpus of documents for the retriever to search over.
**Output:** the fully parsed, structured result object (whatever type the
parser returns) after passing through all four stages — the test asserts this object has the expected fields/content, not just that the pipeline "ran."

### Risks & unknowns
- Unconfirmed: exact mock LLM provider interface (sync vs async, how it's
  injected). Need to read its source before writing step 2.
- Possible async/await mismatches between stages if any component is
  async and others aren't.
- The reranker or generator may depend on config/env vars (e.g. API keys)
  that need to be stubbed or bypassed even with the mock LLM in place.
- Fixture data realism: if my sample documents are too simple, the test might pass trivially without really exercising the reranking logic.

### Edge cases
- For an Empty retrieval results (query matches nothing), the pipeline should fail
  gracefully or return an empty/explicit "no results" parsed output, not throw.
- Reranker receiving fewer documents than it expects to rank.
- Does the parser handle Mock LLM returning malformed or unexpected output without crashing?
- Very short or very long input query strings.
