# Issue #38 Reproduction

**Issue:** [Add an integration test that runs the full RAG pipeline against a mock LLM](https://github.com/ascherj/pathreview/issues/38)

**Branch:** `test/38-rag-pipeline-integration-test`

## Reproduction goal

Issue #38 describes a missing integration test rather than an application crash. The reproduction goal is to confirm that PathReview has tests for individual RAG components but does not have a test that runs one query through retrieval, reranking, generation, and output parsing as a complete workflow.

## Reproduction steps

From the root of the repository, I inspected the integration-test directory:

```bash
ls -la tests/integration
```

The directory contained only:

```text
__init__.py
```

I then checked whether the test file requested by issue #38 exists:

```bash
if [ -f tests/integration/test_rag_pipeline.py ]; then
  echo "test_rag_pipeline.py EXISTS"
else
  echo "REPRODUCED: test_rag_pipeline.py is MISSING"
fi
```

The command returned:

```text
REPRODUCED: test_rag_pipeline.py is MISSING
```

I also ran the integration-test directory:

```bash
.venv/Scripts/python -m pytest tests/integration -v
```

Finally, I ran related unit tests for keyword retrieval, relevance scoring, and output parsing:

```bash
.venv/Scripts/python -m pytest \
  tests/unit/test_keyword_search.py \
  tests/unit/test_relevance_scorer.py \
  tests/unit/test_output_parser.py \
  -v
```

## Observed behavior

The `tests/integration` directory contains only `__init__.py`, and the requested `tests/integration/test_rag_pipeline.py` file is missing. Therefore, pytest cannot collect an integration test that exercises the complete RAG pipeline.

The related unit-test command collected 55 tests. Fifty-two tests passed and three existing tests failed. Those failures concern an empty keyword index, partial-overlap relevance scoring, and JSON-array parsing. They are separate existing problems and are outside the scope of issue #38.

The reproduction confirms that individual RAG components have test coverage, but there is no integration test proving that retrieval, reranking, generation, and parsing work together.

## Expected behavior

PathReview should include a deterministic integration test at:

```text
tests/integration/test_rag_pipeline.py
```

The test should:

1. Submit a representative query.
2. Retrieve relevant document chunks.
3. Order or rerank the retrieved results.
4. Pass the selected context to a mocked LLM.
5. Parse the mock LLM response.
6. Assert that the final structured result is correct.

The test must not make a real external LLM request or require a production API key.

## Reproduction conclusion

Issue #38 is reproducible. PathReview contains separate RAG components and unit tests, but the requested full-pipeline integration test is missing.
