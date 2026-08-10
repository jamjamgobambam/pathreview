## Solution plan

**Issue:** No test verifies that the mock LLM provider returns responses in the expected format — https://github.com/jamjamgobambam/pathreview/issues/108

### Understand
`ingestion/embeddings/provider.py` defines two providers behind one interface: `MockEmbeddingProvider` (used in tests and local dev via `LLM_PROVIDER=mock`) and `OpenAIEmbeddingProvider` (production, calls the OpenAI embeddings API). Expected behavior: the mock can safely stand in for the real provider, so tests that pass with the mock imply the app works with the real one. Actual behavior: `tests/unit/test_llm_provider_contract.py` (27 tests, all passing) exercises the mock in isolation; the only real-provider coverage is `hasattr(OpenAIEmbeddingProvider, 'embed')`. Root cause: no test ever exercises the real provider's `embed()` or compares its response structure against the mock's, so format drift is invisible to the suite.

### Map
- `tests/unit/test_llm_provider_contract.py` — the file the issue names; where the new contract tests go (only file I expect to change)
- `ingestion/embeddings/provider.py` — read-only reference: `EmbeddingProvider` (ABC), `MockEmbeddingProvider`, `OpenAIEmbeddingProvider`, `get_embedding_provider()` factory
- `tests/conftest.py` — read-only reference for the project's fixture patterns

### Plan
1. Add a mocked-OpenAI fixture: patch `openai.OpenAI` with a `MagicMock` whose `embeddings.create` returns a realistic SDK-shaped response (`response.data[i].embedding` = list of floats), so `OpenAIEmbeddingProvider.embed()` runs offline with no API key.
2. Add a `TestProviderContractParity` class asserting, for identical inputs, both providers return: a list, one vector per input text, vectors as lists of Python floats, equal dimensionality (1536), and `[]` for empty input.
3. Add batch-consistency and factory assertions (`get_embedding_provider("mock"/"openai")` both return `EmbeddingProvider` instances).
4. Run the file's tests, then `make check`-equivalent tools on changed files; fix any style/type issues.
5. Commit with a Conventional Commit message referencing #108 and open the PR using the project template.

### Inputs & outputs
Input: lists of text strings (including empty list, batch of 10, identical inputs to both providers). Output: no runtime behavior changes — the deliverable is new test coverage that fails if either provider's response structure diverges (type, count, element type, or dimensionality).

### Risks & unknowns
- Patching at the wrong import point: `OpenAIEmbeddingProvider.__init__` does `from openai import OpenAI`, so the patch must target `openai.OpenAI` (not a module alias) or the real client is constructed.
- The project's strict mypy pre-commit hook requires annotations on all functions, which may force annotating the whole existing test file, not just my additions.
- Pre-existing failures in `make test-unit` / `make lint` on `main` are unrelated to this issue; I must verify my change introduces no new failures rather than trying to fix the repo.

### Edge cases
- Empty input list → both providers must return `[]` (the real provider short-circuits before the API call).
- Batches (10 items) → one vector per input, order and count preserved, all 1536-dim.
- Structure-only assertions: the mock's vectors are hash-derived, so parity tests must compare types/counts/dimensions, not values.
