## Solution plan

**Issue:** Implement an offline eval runner that measures review quality across a benchmark portfolio set. [#40](https://github.com/ascherj/pathreview/issues/40)

### Understand
`scripts/run_evals.py` only has placeholder code right now. It prints fake success messages but does not do any real work. I ran it and confirmed this: no `eval_results.json` file gets created. The issue says the eval logic runs inline during API requests, but that is not true in the current code. `EvalSuite`, `RelevanceScorer`, and `FaithfulnessChecker` are only used in their own tests. They are not connected to the API at all. So there are two problems to fix: there is no standalone runner, and the eval code is not hooked up to the real pipeline either. What should happen: running `python3 scripts/run_evals.py` should run retrieval, then generation, then evaluation, across a set of sample portfolios, and save real scores to `eval_results.json`. What happens now: it prints two lines and stops.

### Map
- `scripts/run_evals.py`: replace the placeholder code with real logic
- `rag/evaluator/eval_suite.py`: already works, just needs to be called
- `rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`, `rag/retriever/keyword_search.py`: handles retrieval
- `rag/generator/review_generator.py`: handles generation, but currently only works with a real API, not a mock one
- `ingestion/embeddings/provider.py`: already has a mock embedding option we can use
- `core/config.py`: loads settings from `.env`
- `tests/benchmarks/`: this folder is empty right now. We need to add sample portfolio files here, or in `tests/fixtures/sample_profiles/` as the placeholder code suggests

### Plan
1. Add a small set of sample portfolios to test with, since none exist yet.
2. Add a mock version of the review generator, similar to the mock embedding provider already in the code, so the script can run without needing a real API key.
3. Update `scripts/run_evals.py` to load the sample portfolios, run retrieval, run generation using the mock version, then run evaluation.
4. Combine the results from all portfolios into one JSON report, with an average score and a score for each portfolio, and save it to `eval_results.json`.
5. Add a test that checks the script creates a proper report from start to finish using the mock versions.

### Inputs & outputs
- Input: sample portfolio files, and settings from `.env` (uses mock mode by default)
- Output: `eval_results.json` with scores for each portfolio and an overall average

### Risks & unknowns
- There is no mock version of the review generator yet. Building one is more work than just connecting existing pieces.
- There are no sample portfolios yet. I will need to decide how many to create and what should be in them.
- The eval code is not connected to the API at all right now. It is unclear if this issue also wants that fixed, or just the standalone script. The issue only asks for the standalone script, so I will stick to that.
- The retriever needs data already loaded into the vector database for each portfolio. The sample portfolios will need to be loaded in first, which is an extra step.

### Edge cases
- A sample portfolio file that is empty or missing data
- A portfolio that gets no matching results back from search
- If one portfolio fails, the whole run should not stop. It should still finish and report results for the portfolios that worked
