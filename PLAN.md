## Solution plan

**Issue:** [#40 — Implement an offline eval runner that measures review quality across a benchmark portfolio set](https://github.com/ascherj/pathreview/issues/40)

Supporting evidence: [docs/reproductions/issue-40-offline-eval-runner.md](docs/reproductions/issue-40-offline-eval-runner.md).
Every claim below is traceable to that reproduction or to a cited file. Where the repository does not
answer a question, it is marked **UNRESOLVED** rather than assumed.

---

### Understand

**What the issue says.** "The current eval suite runs inline during API requests. Add a standalone eval
runner (`scripts/run_evals.py`) that tests the full RAG pipeline against a curated set of benchmark
portfolios and outputs a JSON report of quality scores."

**The issue description does not match the repository's current implementation, and that changes the
shape of the work.** `EvalSuite` does not run inline during API requests — it does not run anywhere. `grep -rn "EvalSuite" --include="*.py" .`
matches only [rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py) itself. The request path
([`process_review`](core/services/review_service.py#L82)) delegates to `_run_ingestion_pipeline`,
`_run_agent_orchestration`, `_run_rag_retrieval_generation`, and `_run_safety_checks`, all of which
return hardcoded literals (e.g. a fixed `"overall_score": 0.81`). So the issue's framing — "move the
inline eval out into a standalone runner" — describes a refactor of wiring that has never existed.

**Root cause.** PathReview has no composition seam for the RAG pipeline at all. Every stage exists as
an isolated unit — `StrategySelector`, `MockEmbeddingProvider`, `VectorStore`, `KeywordSearcher`,
`HybridRetriever`, `ReviewGenerator`, `EvalSuite` — and each was written against an assumed caller
that would assemble them. The only place that assembly was ever supposed to happen is
`process_review()`, which was stubbed out. `scripts/run_evals.py` was scaffolded as the second
intended caller and was likewise never written. Because no code has ever composed these stages
end-to-end, the seams between them were never exercised, and three of them are load-bearing defects:

1. **The vector-indexing seam is broken.** [`VectorStore.add_chunks`](rag/retriever/vector_store.py#L41)
   reads `chunk.id`, `chunk.source_id`, `chunk.chunk_index`, `chunk.section` as *attributes*, but
   [`Chunk`](ingestion/chunking/base.py) is a two-field dataclass (`text`, `metadata`) and the chunkers
   put `source_id`/`chunk_index` inside `metadata`. Calling it raises
   `AttributeError: 'Chunk' object has no attribute 'id'`. It has **zero callers today**, which is
   exactly why the defect survived. A separate, *correct* indexing path exists in
   [`BatchEmbeddingProcessor._store_embedding`](ingestion/embeddings/batch_processor.py) (it reads
   `chunk.metadata[...]`), but it writes to a raw Chroma collection rather than through `VectorStore`,
   so `HybridRetriever` — which reads via `VectorStore` — cannot see anything written that way.
2. **Generation has no offline implementation.** [`ReviewGenerator.__init__`](rag/generator/review_generator.py#L27)
   constructs `openai.OpenAI(...)` eagerly, so it raises `OpenAIError: Missing credentials` before any
   generation call. There is no `get_llm_provider`, `MockGenerator`, or `MockLLM` anywhere in the tree.
   The mock factory that does exist, [`get_embedding_provider`](ingestion/embeddings/provider.py#L103),
   covers embeddings only.
3. **`LLM_PROVIDER` is inert.** `Settings.llm_provider` is declared at [core/config.py:16](core/config.py#L16)
   and CI sets `LLM_PROVIDER: mock` in both [eval.yml](.github/workflows/eval.yml#L23) and
   [ci.yml](.github/workflows/ci.yml#L46), but **no module reads `settings.llm_provider`**, and
   `get_embedding_provider()` has no production callers. The switch CI depends on to stay offline
   currently does nothing.

**So the real task is not "write a script."** It is: introduce the missing offline composition path,
supply the deterministic generation provider that the pipeline lacks, repair the one seam that blocks
composition, and make `LLM_PROVIDER=mock` mean something. `scripts/run_evals.py` is the thin CLI on
top of that — the smallest part of the work.

**Why the runner also cannot reuse `IngestionPipeline`.** [`IngestionPipeline._check_skip`](ingestion/pipeline.py)
calls `self.db_session.query(...)`, so the ingestion orchestrator requires a database session. The
eval job starts no services ([eval.yml](.github/workflows/eval.yml) has no `services:` block), so the
runner must call `StrategySelector.chunk(...)` directly and skip `IngestionPipeline` entirely.

---

### Map

**Files expected to change**

| File | Status | Change |
|---|---|---|
| [scripts/run_evals.py](scripts/run_evals.py) | exists (stub) | Replace the TODO `main()` with a thin CLI: parse args, call the library runner, write `eval_results.json`, set the exit code. |
| `rag/evaluator/benchmark_runner.py` | **new** | The composition seam. `BenchmarkRunner` / `run_benchmarks(...)` drives chunk → embed → index → retrieve → generate → score over all benchmark cases and returns a report dataclass. Lives under `rag/` **because `scripts/` is excluded from the installed distribution** (`pyproject.toml` `[tool.setuptools.packages.find]` `exclude = [... "scripts*"]`; `pathreview.egg-info/top_level.txt` lists only `agent api core ingestion rag safety`). Library code under `scripts/` would resolve only as a CWD namespace package and would not be reliably importable by tests or by an installed copy. |
| `rag/generator/mock_generator.py` | **new** | `MockReviewGenerator` — deterministic, offline, no `openai` import. Same surface as `ReviewGenerator` (`generate_section`, `generate_full_review`) so the two are interchangeable. |
| `rag/generator/provider.py` | **new** | `get_review_generator(provider_name: str)` factory mirroring `get_embedding_provider`, returning `MockReviewGenerator` for `"mock"` and `ReviewGenerator` for `"openai"`/`"openrouter"`. This is where `settings.llm_provider` finally gets read. |
| [rag/retriever/vector_store.py](rag/retriever/vector_store.py) | exists | Fix `add_chunks` to read `source_id`/`chunk_index`/`section` from `chunk.metadata` and derive the id as `f"{source_id}_chunk_{chunk_index}"` (matching `BatchEmbeddingProcessor`'s existing convention). Safe: **zero callers today**, so nothing can regress. |
| `tests/fixtures/sample_profiles/*.json` | **new** | The curated benchmark portfolios. Path chosen because [scripts/run_evals.py:8](scripts/run_evals.py#L8) already names `tests/fixtures/sample_profiles/`. |
| `tests/unit/test_benchmark_runner.py` | **new** | Runner behaviour + determinism + report schema. |
| `tests/unit/test_mock_generator.py` | **new** | Mock generator is deterministic, offline, and grounded in the supplied chunks. |
| [.gitignore](.gitignore) | exists | Add `eval_results.json` — **pending the decision in "Risks & unknowns" Q6.** |

**Context only — read, do not modify**

| File | Why |
|---|---|
| [core/services/review_service.py](core/services/review_service.py) | Establishes that the request path is stubbed and `EvalSuite` is uncalled. Explicitly out of scope; the issue does not ask for request-time evaluation. |
| [api/routes/reviews.py](api/routes/reviews.py), `api/schemas/` | API behaviour must not change. |
| [ingestion/pipeline.py](ingestion/pipeline.py) | DB-coupled; bypassed, not refactored. |
| [rag/generator/review_generator.py](rag/generator/review_generator.py) | The real generator stays as-is; the mock is added alongside it rather than by modifying it. |
| [rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py), [relevance_scorer.py](rag/evaluator/relevance_scorer.py), [faithfulness_checker.py](rag/evaluator/faithfulness_checker.py) | Already deterministic and offline; called as-is. Modified **only** if actionability is ruled in (Q1). |
| [rag/retriever/hybrid.py](rag/retriever/hybrid.py), [keyword_search.py](rag/retriever/keyword_search.py) | Used as-is. Its silent-degradation behaviour is handled by the runner, not by editing it (see Q7). |
| [ingestion/chunking/](ingestion/chunking/), [ingestion/embeddings/provider.py](ingestion/embeddings/provider.py) | Used as-is. |
| [.github/workflows/eval.yml](.github/workflows/eval.yml) | Defines the contract; the runner conforms to it rather than the reverse. |
| [docker-compose.yml](docker-compose.yml), [Dockerfile](Dockerfile) | The runner must not depend on containers. Not modified. |

---

### Plan

**Step 1 — Add a deterministic, offline generation provider.**
Create `rag/generator/mock_generator.py` with `MockReviewGenerator`, matching `ReviewGenerator`'s
public surface (`generate_section(section_name, context_chunks, profile_data) -> FeedbackSection`,
`generate_full_review(profile_data, retrieved_chunks) -> list[FeedbackSection]`) and reusing
[`FeedbackSection`](rag/generator/output_parser.py). It must import no networking library.

The critical design constraint: **the mock's output must be derived from the retrieved chunks.**
[`FaithfulnessChecker.check`](rag/evaluator/faithfulness_checker.py) scores the fraction of feedback
sentences sharing ≥2 non-stopword tokens with the concatenated context. A mock returning canned
lorem-ipsum would score ~0.0 faithfulness on every benchmark, making the metric a constant and the
whole report worthless as a regression signal. The mock will therefore compose each section's text
from salient terms taken from the top-ranked chunks, using a fixed, seeded, order-stable procedure so
identical inputs yield identical strings. Then create `rag/generator/provider.py` with
`get_review_generator(provider_name)`, mirroring `get_embedding_provider`'s shape (lowercase/strip,
`ValueError` on unknown names).

**Step 2 — Repair the `Chunk` → `VectorStore` seam.**
Change [`VectorStore.add_chunks`](rag/retriever/vector_store.py#L41) to read `source_id`,
`chunk_index`, and `section` from `chunk.metadata`, deriving `id` as
`f"{source_id}_chunk_{chunk_index}"` — the identifier convention
`BatchEmbeddingProcessor._store_embedding` already uses, so the two indexing paths converge instead of
diverging. This is a prerequisite for the runner: without it, `add_chunks` raises `AttributeError` and
`HybridRetriever` has nothing to read. Justified as in-scope because it is on the critical path, is
confined to `rag/` (the issue's own label), and has zero existing callers.

**Step 3 — Author the benchmark portfolio fixtures.**
Add 3–5 JSON files under `tests/fixtures/sample_profiles/`, each one portfolio with its documents and
its eval queries (schema in "Inputs & outputs"). Content will be synthetic and PII-free, modelled on
the existing `sample_resume_text` / `sample_readme_text` fixtures in
[tests/conftest.py](tests/conftest.py). They must be deliberately varied — a strong portfolio, a
sparse one, a mismatched-query one — so aggregate scores can move when retrieval or generation
regresses. Corpus size matters: §4.4 of the reproduction shows BM25 returns negative scores on a
single-document corpus, so each portfolio needs enough chunks to keep BM25 well-behaved.

**Step 4 — Build the offline pipeline runner.**
Create `rag/evaluator/benchmark_runner.py`. Per benchmark portfolio:
1. Load and validate the fixture (fail loudly on a malformed fixture — see "Edge cases").
2. `StrategySelector().chunk(doc_text, metadata)` for each document — **not** `IngestionPipeline`.
3. `get_embedding_provider(settings.llm_provider)` → `.embed([...])`.
4. Index into an **ephemeral** `VectorStore(persist_dir=<tempfile.TemporaryDirectory()>)` via the
   now-fixed `add_chunks`, into a per-portfolio collection `f"profile_{portfolio_id}"`.
5. `KeywordSearcher().index(chunk_dicts)` — **mandatory**, and each dict must carry an `"id"` key
   matching the vector-store id. Reproduction §4.2 shows that skipping this, or omitting `"id"`,
   silently zeroes the BM25 half of every blended score without raising.
6. `HybridRetriever(vector_store, keyword_searcher).retrieve(query, portfolio_id, query_embedding,
   max_chunks=settings.max_chunks_per_query, min_score=settings.min_relevance_score)`.
7. `get_review_generator(settings.llm_provider).generate_full_review(profile_data, chunks)`.
8. `EvalSuite().run(query, chunks, feedback)` per query, where `feedback` is the concatenated section
   content. This resolves the one-query/many-sections mismatch: `EvalSuite.run` takes a single query,
   so the runner scores **per query** and aggregates per portfolio.
9. Aggregate per portfolio, then across the portfolio set.

**Step 5 — Rewrite `scripts/run_evals.py` as a thin CLI.**
`main()` calls the library runner, serialises the report with `json.dump(..., indent=2, sort_keys=True)`
to `eval_results.json` at the repository root (what [eval.yml](.github/workflows/eval.yml) reads), and
prints a short human summary. It must write the file **before** any threshold check, so CI can publish
results even on a failing run. Delete the misleading unconditional
`print("Evaluation complete. Results written to eval_results.json")`. Add `--output` and
`--fixtures-dir` flags for local use, defaulting to the CI-expected paths. Exit-code policy is
**UNRESOLVED** (Q3) — until it is settled, exit 0 on a completed run and non-zero only on an actual
error (missing fixtures, unreadable JSON, an exception mid-pipeline).

**Step 6 — Tests.**
Following the existing conventions (`@pytest.mark.unit`, class-per-subject, fixture methods, as in
[tests/unit/test_relevance_scorer.py](tests/unit/test_relevance_scorer.py)):
- `test_mock_generator.py` — deterministic output, no network, sections grounded in supplied chunks.
- `test_benchmark_runner.py` — runs a tiny inline fixture end-to-end; asserts the report schema; runs
  twice and asserts byte-identical JSON; asserts a malformed fixture raises rather than silently
  scoring 0.
- All new tests must pass. **No deliberately failing test will be committed.**

**Step 7 — Verify.** `make check` (ruff + black + mypy — note `disallow_untyped_defs = true`, so every
new function needs annotations) and `make test-unit`. Then run `LLM_PROVIDER=mock python
scripts/run_evals.py` twice with no Docker services running and `diff` the two `eval_results.json`
outputs to prove determinism.

---

### Inputs & outputs

**Input — benchmark portfolio fixture (proposed; schema is UNRESOLVED, Q4).**
No benchmark schema exists anywhere in the repository, so this is a proposal derived from what the
pipeline actually consumes: `StrategySelector.chunk` needs `source_type` and `source_id` in metadata;
`ReviewGenerator.generate_section` reads `github_username` and `projects` from `profile_data`;
`EvalSuite.run` needs a query string.

```json
{
  "portfolio_id": "bench01",
  "description": "Backend-leaning junior portfolio with a strong resume and one thin README",
  "profile": {
    "github_username": "janedoe",
    "projects": [{ "name": "weather-app", "language": "TypeScript" }]
  },
  "documents": [
    { "source_id": "resume_bench01", "source_type": "resume", "text": "..." },
    { "source_id": "readme_bench01_weather", "source_type": "readme", "text": "..." }
  ],
  "queries": [
    "Python FastAPI backend REST API experience",
    "project documentation and README quality"
  ]
}
```

Deliberately **not** included: expected/golden scores. There is no evidence in the repository for what
a "good" score is, and baking in invented numbers would create a false gate (Q2).

**Output — `eval_results.json` (proposed; format is UNRESOLVED, Q5).**
The only hard constraint from the repository is that [eval.yml](.github/workflows/eval.yml) reads the
file at the repo root and embeds its **entire contents** verbatim in a PR comment inside a ```` ```json ````
fence. That implies the report must stay small and human-legible — a full dump of retrieved chunk text
would produce an unreadable comment. Proposed:

```json
{
  "schema_version": 1,
  "generated_by": "scripts/run_evals.py",
  "llm_provider": "mock",
  "portfolio_count": 4,
  "query_count": 8,
  "aggregate": {
    "relevance_score": 0.612,
    "faithfulness_score": 0.845,
    "overall_score": 0.728
  },
  "portfolios": [
    {
      "portfolio_id": "bench01",
      "chunk_count": 7,
      "queries": [
        {
          "query": "Python FastAPI backend REST API experience",
          "retrieved_count": 5,
          "relevance_score": 0.667,
          "faithfulness_score": 0.900,
          "overall_score": 0.783
        }
      ],
      "relevance_score": 0.640,
      "faithfulness_score": 0.880,
      "overall_score": 0.760
    }
  ]
}
```

Notes: field names mirror `EvalResult`'s (`relevance_score`, `faithfulness_score`, `overall_score`) so
the report and the dataclass do not drift. No timestamp, hostname, git SHA, or duration is included —
those would change every run and destroy byte-level reproducibility. Floats are rounded to a fixed
precision at serialisation to avoid platform-dependent trailing digits. `schema_version` is included
so a future change to the report is detectable by consumers.

**How determinism, offline operation, and CI-safety are guaranteed**

| Property | Mechanism | Evidence |
|---|---|---|
| No network | `MockReviewGenerator` imports no HTTP client; `MockEmbeddingProvider` is pure SHA-256 + NumPy; `ReviewGenerator` is never constructed when `llm_provider == "mock"` (construction, not just calls, is what raises `OpenAIError`). | Reproduction §2.4 |
| No external services | Embedded `chromadb.PersistentClient` pointed at a `TemporaryDirectory`; BM25 in-memory; no Postgres/Redis; `IngestionPipeline` bypassed. | Reproduction §4, [eval.yml](.github/workflows/eval.yml) has no `services:` |
| Deterministic scoring | `RelevanceScorer` and `FaithfulnessChecker` are pure lexical overlap — no RNG, no model. | Reproduction §4 table |
| Deterministic embeddings | `MockEmbeddingProvider` seeds `np.random.RandomState` from a SHA-256 of the text. | Verified: identical vectors across runs |
| Deterministic generation | Mock composes text from chunks by a fixed, order-stable rule; retrieval results are sorted before use so tie order cannot vary. | Step 1 |
| Deterministic output bytes | `sort_keys=True`, fixed float rounding, no timestamps/paths in the report. | "Output" above |
| Leaves no repo residue | Vector store writes to a temp dir, never `.chromadb/` in the working tree. | — |
| `LLM_PROVIDER` honoured | `get_review_generator(settings.llm_provider)` and `get_embedding_provider(settings.llm_provider)` — the first production readers of that setting. | Reproduction §2.5 |
| Python 3.11 | No syntax newer than 3.11; `make check` runs mypy pinned at `python_version = "3.11"`. | [pyproject.toml](pyproject.toml) |

---

### Risks & unknowns

**Unresolved — no repository evidence answers these. They will be raised on the issue rather than
silently decided.**

- **Q1 — Is actionability in scope?** [scripts/run_evals.py:10](scripts/run_evals.py#L10) lists
  "relevance, faithfulness, and actionability", but `actionab` matches **only that comment** across
  every `.py` file, and `EvalSuite` computes `overall = (relevance + faithfulness) / 2`
  ([eval_suite.py:46](rag/evaluator/eval_suite.py#L46)). Adding a third metric means changing
  `EvalSuite` and the meaning of `overall_score`. **Default if unanswered:** implement relevance +
  faithfulness only, matching the code, and note the omission in the PR — a scorer invented here would
  be measuring a definition nobody agreed to.
- **Q2 — What score thresholds define success?** No thresholds, golden outputs, or baselines exist
  anywhere. **Default:** report scores, gate nothing.
- **Q3 — Should the runner exit non-zero below threshold?** Depends on Q2. `eval.yml` has no
  `continue-on-error`, so a non-zero exit would fail the job *and* skip the comment step (which is
  gated on `if: github.event_name == 'pull_request'`, not on success) — turning a quality signal into
  a hard merge block. **Default:** exit 0 on a completed run.
- **Q4 — Benchmark schema and location.** Proposed above; `tests/fixtures/sample_profiles/` is taken
  from the existing TODO, but nothing else about the format is specified.
- **Q5 — `eval_results.json` schema.** The only constraint is that `eval.yml` inlines the whole file
  into a PR comment.
- **Q6 — Should `eval_results.json` be committed or ignored?** It is not currently in
  [.gitignore](.gitignore). Committing it creates diff noise on every run and invites stale reports;
  ignoring it is cleaner but loses the historical baseline that would make trends visible. **Leaning:**
  git-ignore it and treat it as a CI artifact.
- **Q7 — How faithful must "the full RAG pipeline" be?** The plan drives the real `StrategySelector`,
  `VectorStore`, `KeywordSearcher`, `HybridRetriever`, and `EvalSuite`, substituting deterministic
  providers only at the two model boundaries (embeddings, generation). Whether the maintainer expects
  more (e.g. the parsers, the agent, the safety layer) is unconfirmed.

**Risks**

- **The scores may measure plumbing rather than quality.** Reproduction §4.3: under
  `MockEmbeddingProvider`, cosine similarity to a paraphrase is +0.054 versus +0.000 for unrelated
  text — vectors are effectively orthogonal, so vector ranking is close to random and BM25 carries all
  real signal. The report is therefore a **regression and determinism** signal, not a semantic-quality
  measurement. This limitation must be stated in the report or the PR rather than papered over; a
  number labelled "review quality" that is 70% noise is worse than no number.
- **A mock generator can make faithfulness meaningless in either direction.** Canned text pins it near
  0.0; text copied verbatim from the chunks pins it near 1.0. Both are constants that detect nothing.
  Mitigation: derive text from chunks but paraphrase/recombine, and add a test asserting the metric
  actually varies across benchmarks of differing quality.
- **Scope creep into the request path.** The mismatch between the issue description and the current
  implementation invites "fix `process_review` too". Out of scope;
  `core/services/review_service.py` will not be touched.
- **Fixing `add_chunks` touches shared code.** Mitigated by it having zero callers and by aligning it
  with the id convention `BatchEmbeddingProcessor` already uses.
- **Python version skew.** CI is 3.11; the local `.venv` is 3.14.0. Anything relying on 3.12+ behaviour
  would pass locally and fail in CI. Mitigated by mypy's `python_version = "3.11"` and by avoiding new
  syntax.
- **Chroma writing into the working tree.** `VectorStore`'s default `persist_dir=".chromadb"` would
  leave an untracked directory (and a stale collection that could poison a later run). Mitigated by
  always passing an explicit temp dir.
- **The eval job may not even run on the eventual PR.** Its `paths:` filter covers `rag/**`,
  `ingestion/chunking/**`, `ingestion/embeddings/**` — a PR touching only `scripts/` and `tests/`
  would not trigger it. This plan does change `rag/`, so it should trigger; worth confirming.

---

### Edge cases

**Failure cases the runner must handle explicitly**

| Case | Current behaviour | Required behaviour |
|---|---|---|
| Fixtures directory missing or empty | N/A (feature absent) | Exit non-zero with a clear message. Must **not** write a report full of zeros — that reads as "quality collapsed" rather than "nothing ran". This is precisely the failure mode of today's stub. |
| A fixture file is malformed JSON or missing `documents`/`queries` | N/A | Fail loudly, naming the file. Skipping it silently would shrink the benchmark set and shift the aggregate without explanation. |
| A document produces zero chunks (empty/whitespace text) | `KeywordSearcher.index([])` leaves `self.bm25 = None`; `.search` then logs `keyword_search_empty_index` and returns `[]` | Detect and fail at fixture-validation time. |
| Retrieval returns zero chunks (everything below `min_score`) | `RelevanceScorer.score` returns `0.0`; `FaithfulnessChecker.check` returns `0.0` on empty chunks | Record the query with `retrieved_count: 0` and an explicit flag, so a retrieval failure is distinguishable from genuinely bad relevance. |
| Keyword index not built, or chunk dicts lack `"id"` | Blended score silently drops to vector-only; **no error** (reproduction §4.2, CASE A ≡ CASE D) | Runner always indexes and always sets `"id"`; a test asserts a non-zero `keyword_score` on a known-matching query so this cannot regress unnoticed. |
| Single-document / tiny corpus | BM25 returned **−0.824**; a negative `keyword_scores_max` inverts the normalisation and `min_score=0.3` can discard everything (reproduction §4.4) | Require a minimum chunk count per portfolio at validation time; assert in tests that no benchmark yields negative BM25. |
| `feedback` has no sentence longer than 10 characters | `FaithfulnessChecker._extract_claims` returns `[]` → `check` returns the neutral **0.5**, not 0.0 | Ensure mock sections are long enough that 0.5 never appears as an accidental constant. |
| Query with no tokens (empty string) | `RelevanceScorer.score` returns `0.0` | Reject empty queries at fixture validation. |
| Feedback longer than 10 sentences | `_extract_claims` truncates to the first 10 claims | Harmless but worth knowing: faithfulness is computed over at most 10 sentences, so very long sections dilute nothing but also measure nothing beyond the tenth. |
| More than 10 retrieved chunks | `ReviewGenerator._format_context` truncates context to 10 chunks, while `EvalSuite` scores **all** retrieved chunks | Cap retrieval at `settings.max_chunks_per_query` (default 10) so the generator and the scorer see the same set; otherwise faithfulness is scored against context the generator never saw. |
| `LLM_PROVIDER` unset, or set to `openai` | Nothing reads it today | `get_review_generator` raises `ValueError` on unknown names; when it resolves to a live provider the runner must refuse to run unless a key is present, rather than crashing mid-benchmark with `OpenAIError`. |
| Stale Chroma collection from a previous run | `VectorStore.get_collection` returns the existing collection and `add_chunks` upserts into it | Fresh `TemporaryDirectory` per run guarantees isolation. |
| Duplicate `source_id` + `chunk_index` across documents | Ids collide; `upsert` silently overwrites, shrinking the corpus | Validate id uniqueness after chunking and fail on collision. |
| Two runs producing different bytes | N/A | A test runs the pipeline twice and asserts identical serialised output — the single strongest guard for the issue's core promise. |
