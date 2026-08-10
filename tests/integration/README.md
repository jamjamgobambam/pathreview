# Integration test reproduction

Issue [#38](https://github.com/ascherj/pathreview/issues/38) asks for an
integration test that exercises retrieval, score-based reranking, generation
with a mock LLM, and output parsing.

## Reproduction

From the repository root, run:

```bash
pytest --collect-only -q tests/integration
```

Observed on July 28, 2026:

```text
no tests collected in 0.01s
```

The `tests/integration` package contains no test module, so pytest cannot
exercise any part of the RAG pipeline as an integrated flow. Existing tests
cover individual components under `tests/unit`, but none pass retrieved chunks
through `ReviewGenerator` and `parse_review_output`.

Code inspection also confirms that `ingestion/embeddings/provider.py` provides
a deterministic `MockEmbeddingProvider`, while the generation path in
`rag/generator/review_generator.py` directly constructs an OpenAI client and
has no corresponding mock LLM provider. The integration test will therefore
need to replace that client boundary with a deterministic fake response.
