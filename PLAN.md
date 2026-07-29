## Solution plan

**Issue:** [Implement an offline eval runner that measures review quality across a benchmark portfolio set](https://github.com/ascherj/pathreview/issues/40)

### Understand

The repository already has the individual building blocks for evaluation.
`IngestionPipeline` parses and embeds resume, README, and repository inputs;
`HybridRetriever.retrieve()` combines vector and BM25 results;
`ReviewGenerator.generate_full_review()` produces five feedback sections; and
`EvalSuite.run()` returns an `EvalResult` containing `relevance_score`,
`faithfulness_score`, and their mean as `overall_score`.

The issue describes evaluation as running inline during API requests. The
inspected branch does not currently demonstrate that behavior: the request path
is `api.routes.reviews.create_review_endpoint()` to the background
`core.services.review_service.process_review()` task, which calls
`_run_ingestion_pipeline()`, `_run_agent_orchestration()`, and
`_run_rag_retrieval_generation()`. Those helpers return placeholder data;
`_run_rag_retrieval_generation()` does not instantiate the concrete retriever or
generator, and the codebase has no `EvalSuite` call site. The `overall_score`
stored on `Review` is therefore the placeholder RAG output's score, not an
`EvalResult`.

The requested standalone behavior is also absent. `scripts/run_evals.py` prints
start and completion messages around TODO comments, accepts no paths, loads no
benchmarks, runs no pipeline or evaluator, handles no per-case failures, and
writes no JSON. Running it with `python3 scripts/run_evals.py` exited successfully
while `eval_results.json` remained absent.

Expected behavior is a command that validates curated local portfolio cases,
runs each through the same ingestion, retrieval, and generation boundary used by
the application, passes the resulting query, retrieved chunks, and generated
feedback to `EvalSuite`, continues after individual case failures, aggregates
successful scores, and writes a machine-readable report. The likely
architectural boundary is a reusable RAG pipeline service under `rag/`, called
both by `process_review()` and the offline runner. Keeping benchmark/report
orchestration in `scripts/run_evals.py` prevents CLI concerns from entering the
API service.

### Map

- `scripts/run_evals.py` — **modify.** Replace the placeholder `main()` with CLI
  parsing, benchmark loading and validation, per-case execution, failure
  isolation, aggregation, JSON serialization, and output-path handling.
- `rag/evaluator/eval_suite.py` — **reuse; modify only if a stable serialization
  helper or explicit score schema is needed.** `EvalSuite.run(query, chunks,
  feedback)` is the scoring boundary, and `EvalResult` defines the actual three
  score names. Python's dataclass serialization may be sufficient without
  changing this file.
- `api/routes/reviews.py` — **reuse only for request-path verification.**
  `create_review_endpoint()` creates a `Review` and schedules
  `process_review()`; the offline CLI should not call the HTTP route or require
  authentication.
- `core/services/review_service.py` — **modify to consume the shared pipeline
  boundary.** `process_review()` is the application entry point;
  `_run_ingestion_pipeline()` currently creates and commits `IngestedSource`
  rows, while `_run_rag_retrieval_generation()` is a placeholder. The latter
  should delegate to the same reusable pipeline invoked by the offline runner
  instead of maintaining a second implementation.
- `rag/pipeline.py` — **proposed new file.** Add a reusable, dependency-injected
  `RAGPipeline` (or equivalent function) that coordinates ingestion/embedding,
  query embedding, `HybridRetriever.retrieve()`, and
  `ReviewGenerator.generate_full_review()`, then returns both retrieved chunks
  and generated sections. The exact public name should be fixed before tests so
  the API and CLI share one entry point.
- `ingestion/pipeline.py` — **reuse.** `IngestionPipeline.ingest_resume()`,
  `ingest_readme()`, and `ingest_repo_metadata()` are the concrete local-source
  ingestion methods. They require vector database and database-session
  dependencies, which the offline boundary must isolate from production state.
- `ingestion/embeddings/provider.py` — **reuse.**
  `MockEmbeddingProvider.embed()` supplies deterministic 1,536-dimensional
  embeddings suitable for offline tests; `get_embedding_provider()` supports
  the configured provider selection.
- `rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`, and
  `rag/retriever/keyword_search.py` — **reuse.** `HybridRetriever.retrieve()` is
  the concrete retrieval operation. Its `KeywordSearcher` must be indexed with
  the collection's chunks, and its `VectorStore` should use an isolated
  temporary persistence directory during offline runs.
- `rag/generator/review_generator.py` — **reuse, with dependency injection likely
  required.** `ReviewGenerator.generate_full_review()` is the concrete
  generation operation and returns generator `FeedbackSection` dataclasses.
  The class currently always constructs an OpenAI-compatible client, so a
  deterministic generation substitute or injectable client is needed for
  credential-free tests.
- `core/models/profile.py` and `api/schemas/profile.py` — **reuse as the current
  portfolio schema references.** `Profile` stores `github_username`,
  `portfolio_url`, `resume_filename`, and `resume_text`; `ProfileCreate` exposes
  only the first two fields because resume content arrives as multipart form
  data in `api/routes/profiles.py`.
- `core/models/review.py` and `api/schemas/review.py` — **reuse as application
  output references.** They define stored review sections and one
  `overall_score`, which must not be confused with the evaluator's three quality
  scores.
- `tests/benchmarks/portfolios/*.json` — **proposed benchmark location and new
  fixtures.** `tests/benchmarks/` currently contains only `__init__.py`; no
  curated portfolios exist. The stale TODO path
  `tests/fixtures/sample_profiles/` also does not exist.
- `tests/unit/test_relevance_scorer.py`,
  `tests/unit/test_faithfulness_checker.py`,
  `tests/unit/test_llm_provider_contract.py`,
  `tests/unit/test_output_parser.py`, and
  `tests/unit/test_review_service.py` — **reuse as test conventions.** They show
  the `pytest.mark.unit` convention, deterministic embedding expectations,
  evaluator edge behavior, generator output shape, and async service mocking.
- `tests/unit/test_run_evals.py` — **proposed new file.** Test case validation,
  duplicate detection, aggregation, JSON serialization, output failures, and
  partial failures with injected fake pipeline/evaluator dependencies.
- `tests/integration/test_offline_eval_pipeline.py` — **proposed new file.** Run a
  small curated case through the shared pipeline with deterministic embeddings,
  an isolated vector store, and a fake generator, then assert retrieval,
  generation, evaluation, and report data are connected end to end.
- `.github/workflows/eval.yml` and `Makefile` — **reuse, with a possible workflow
  adjustment after the CLI contract is fixed.** Both already invoke
  `scripts/run_evals.py`; the workflow sets `LLM_PROVIDER=mock` and then reads
  `eval_results.json`.

### Plan

1. **Define and validate benchmark cases.** Add curated local JSON cases under
   `tests/benchmarks/portfolios/` using fields for a unique case `id`, evaluation
   `query`, profile metadata, and embedded local sources such as resume text,
   README content, and repository metadata. Implement loading and schema
   validation helpers in `scripts/run_evals.py`, rejecting a missing/empty input
   path, malformed JSON, unsupported source types, missing required fields, and
   duplicate IDs before expensive work begins.
2. **Create one executable full-RAG boundary.** Add the dependency-injected
   service in `rag/pipeline.py` using `IngestionPipeline`,
   `MockEmbeddingProvider` or the configured embedding provider,
   `HybridRetriever.retrieve()`, and
   `ReviewGenerator.generate_full_review()`. Refactor
   `core.services.review_service._run_rag_retrieval_generation()` to call it.
   Return the query, retrieved chunks, and generated sections needed for
   evaluation, while allowing offline storage/client substitutes so benchmark
   runs do not write production database or vector state.
3. **Score every completed case.** In `scripts/run_evals.py`, flatten generated
   section content into the feedback string required by `EvalSuite.run()`, retain
   each `EvalResult` under the matching case ID, and record retrieval/generation
   failures separately. Use the evaluator's real `relevance_score`,
   `faithfulness_score`, and `overall_score` fields; do not introduce the TODO's
   actionability score unless a separate issue defines and implements it.
4. **Aggregate and write the report.** Add CLI options such as `--input` and
   `--output`, calculate averages over successful cases only, include successful
   and failed counts, and emit valid JSON to the requested path. Create missing
   parent directories when allowed, write through a temporary file followed by
   replacement to avoid a truncated report, report case errors without aborting
   the remaining set, return a nonzero exit status for configuration/output
   failures, and define an explicit policy for partial case failures.
5. **Add deterministic verification.** In `tests/unit/test_run_evals.py`, inject
   fake pipeline and evaluator results to cover loading, aggregation,
   serialization, path handling, duplicate IDs, and partial failure behavior. In
   `tests/integration/test_offline_eval_pipeline.py`, use
   `MockEmbeddingProvider`, a temporary vector store, and a fake generator to
   prove that a curated fixture reaches retrieval, generation, and `EvalSuite`.
   Run the focused tests, existing evaluator/retrieval/generation tests, the
   unit suite, and the CLI against a temporary output path.

### Inputs & outputs

The default input is proposed as the directory
`tests/benchmarks/portfolios/`, with `--input` accepting either that directory or
an explicitly documented manifest file. Every case should be self-contained so
offline runs do not fetch a live GitHub account or portfolio URL. A proposed
case schema is:

```json
{
  "id": "backend-python-baseline",
  "query": "Review this portfolio for backend engineering readiness.",
  "profile": {
    "github_username": "benchmark-user",
    "portfolio_url": null,
    "resume_filename": "resume.md",
    "resume_text": "Curated resume text",
    "projects": [
      {
        "name": "sample-api",
        "github_repo": "benchmark-user/sample-api"
      }
    ]
  },
  "sources": [
    {
      "type": "readme",
      "repo_name": "sample-api",
      "content": "# Sample API\nCurated README content"
    },
    {
      "type": "repo",
      "data": {
        "name": "sample-api",
        "language": "Python"
      }
    }
  ]
}
```

This is proposed rather than an existing contract: neither
`tests/benchmarks/` nor `tests/fixtures/sample_profiles/` currently supplies a
portfolio schema. The loader should align shared profile fields with
`core.models.profile.Profile` while keeping local source content explicit for
`IngestionPipeline`.

Runtime configuration includes input/output paths, embedding and generation
provider selection, retrieval limits from `core.config.settings`
(`max_chunks_per_query` and `min_relevance_score`), a temporary vector-store
location, and any model/base URL/API key needed by a non-mock generator. The
CI workflow currently sets `LLM_PROVIDER=mock`, but the repository has only a
mock embedding provider, not a mock `ReviewGenerator`; implementation must make
that mode concrete before relying on it. Real-provider runs may require
`OPENAI_API_KEY` or `OPENROUTER_API_KEY` and network access.

The default output expected by the existing Makefile/workflow is
`eval_results.json`, with `--output` allowing another path. Generated reports
must remain uncommitted. The following report shape is **proposed** because no
formal report schema exists:

```json
{
  "metadata": {
    "generated_at": "2026-07-29T18:00:00Z",
    "case_count": 2,
    "input_path": "tests/benchmarks/portfolios",
    "provider": "mock"
  },
  "cases": [
    {
      "id": "backend-python-baseline",
      "status": "passed",
      "retrieved_chunk_count": 6,
      "scores": {
        "relevance_score": 0.75,
        "faithfulness_score": 0.8,
        "overall_score": 0.775
      },
      "error": null
    },
    {
      "id": "frontend-invalid",
      "status": "failed",
      "retrieved_chunk_count": 0,
      "scores": null,
      "error": {
        "stage": "generation",
        "message": "Sanitized error summary"
      }
    }
  ],
  "summary": {
    "successful_cases": 1,
    "failed_cases": 1,
    "average_scores": {
      "relevance_score": 0.75,
      "faithfulness_score": 0.8,
      "overall_score": 0.775
    }
  }
}
```

Average scores should be `null` when no case succeeds rather than inventing a
zero-quality result. Timestamps should be UTC ISO 8601 strings, score values
plain JSON numbers, ordering deterministic for stable tests, and errors
sanitized so credentials or raw sensitive portfolio text are never included.

### Risks & unknowns

- **The issue premise and current call graph disagree.**
  `core.services.review_service.process_review()` calls a placeholder
  `_run_rag_retrieval_generation()`, and `EvalSuite` has no call sites.
  Establishing a truly shared production/offline path may therefore be larger
  than wiring the existing script.
- **Generation has no implemented mock provider.** `core/config.py` defaults
  `llm_provider` to `mock` and `.github/workflows/eval.yml` sets it, but
  `ReviewGenerator.__init__()` always creates an OpenAI-compatible client.
  Credential-free CI needs an injected fake/deterministic generator or a real
  mock provider contract.
- **Real model dependencies are nondeterministic, slow, and potentially
  expensive.** `ReviewGenerator.generate_section()` makes five chat completion
  calls per full review at temperature `0.7`. Repeated benchmark results may
  vary and consume API quotas; provider, model, temperature, and prompt version
  should be captured in metadata.
- **Embedding and retrieval storage can change local state.**
  `IngestionPipeline` writes embeddings through `BatchEmbeddingProcessor`, and
  `VectorStore` defaults to persistent `.chromadb`. Offline runs need an isolated
  temporary collection/directory and cleanup policy, especially after
  interruption.
- **The two ingestion paths are inconsistent.**
  `review_service._run_ingestion_pipeline()` creates and commits
  `IngestedSource` records with placeholder raw data, while
  `IngestionPipeline` operates synchronously and its database deduplication query
  is marked as a placeholder. The shared pipeline must define whether offline
  runs use a fake session or bypass persistence without changing production
  records.
- **Portfolio input has no single schema.** `core.models.profile.Profile` stores
  resume text, filename, GitHub username, and portfolio URL;
  `api.schemas.profile.ProfileCreate` omits resume content because the route
  receives it as a file; and `ReviewGenerator` additionally expects a `projects`
  list. The benchmark contract must reconcile those inputs explicitly.
- **The report contract and failure exit policy are unspecified.**
  `scripts/run_evals.py` names `eval_results.json`, and
  `.github/workflows/eval.yml` reads it, but no schema says whether partial case
  failure should make the process nonzero or what empty averages mean.
- **The requested metric set is ambiguous.** `EvalSuite` returns relevance,
  faithfulness, and overall only, while the script TODO mentions actionability.
  Adding a new metric requires a definition, scorer, and tests rather than
  silently placing a fabricated field in the report.
- **Evaluator inputs may discard useful structure.** `EvalSuite.run()` accepts
  one feedback string, but `ReviewGenerator.generate_full_review()` returns a
  list of sections. Concatenating section content is a proposed adapter; it is
  unknown whether scores should instead be per section and then aggregated.
- **Current scorers are lexical heuristics.** `RelevanceScorer` averages query
  token overlap across chunks, and `FaithfulnessChecker` uses two meaningful
  overlapping tokens as support. Quality thresholds must be calibrated against
  curated expected behavior before treating these values as regression gates.
- **Generated reports are not currently ignored.** `.gitignore` does not list
  `eval_results.json`; implementation should add the report path or pattern so a
  normal run does not accidentally stage generated output.

### Edge cases

- The benchmark directory exists but contains no cases: write no misleading
  averages and return a documented configuration error.
- The default fixture directory is missing: identify the resolved input path and
  fail before initializing model or storage dependencies.
- A JSON document is malformed, has an unsupported root type, or contains
  invalid portfolio data: report the file and validation problem without
  exposing its full content.
- A case lacks `id`, `query`, required profile/source fields, resume filename, or
  source content: reject it during validation.
- Two files define the same case ID: fail validation so results cannot overwrite
  or ambiguously aggregate one another.
- A benchmark has no sources or ingestion produces no chunks: either record a
  failed ingestion/retrieval stage or deliberately evaluate zero relevance,
  according to the documented policy.
- Retrieval returns no chunks after `min_relevance_score` filtering: generation
  must not pretend it has evidence, and the report should retain the zero-chunk
  count.
- One section generation fails but `generate_full_review()` returns its
  zero-confidence error section: define whether that is a failed case or a
  completed case with degraded output.
- All generation fails, the provider times out, returns empty content, or returns
  malformed output: record a sanitized generation error and continue other
  cases.
- `EvalSuite.run()` raises, returns an out-of-range/non-finite score, or receives
  empty feedback: mark only that case failed and exclude it from averages.
- One case fails among successful cases: retain both case records, average only
  valid successes, and apply the documented partial-failure exit policy.
- The output file already exists: replace it atomically only after the new report
  serializes successfully.
- The output parent directory is missing: create it when valid and permitted, or
  return a clear output error.
- The output path is unwritable, is a directory, or resides outside allowed
  locations: fail without losing an existing report.
- A score is a NumPy scalar, dataclass, `NaN`, infinity, or another
  non-JSON-serializable value: normalize finite floats and reject invalid values
  before writing.
- Required credentials are missing for the selected real provider: fail during
  configuration before processing cases; mock mode should require none.
- The evaluation is interrupted: do not leave a partial final report or
  persistent benchmark collection; clean temporary resources and preserve any
  previous valid report.
