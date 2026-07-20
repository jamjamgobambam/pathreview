# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/40

**Issue title:** Implement an offline eval runner that measures review quality across a benchmark portfolio set

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Today PathReview's review-quality evaluation exists only as an in-process `EvalSuite` in `rag/evaluator/` that scores a single query's retrieved chunks and generated feedback for relevance and faithfulness, designed to run inline with request-time review generation rather than as an independent, repeatable job. There is no offline harness that drives the full retrieval-and-generation pipeline over a fixed benchmark set: `scripts/run_evals.py` is currently a stub whose `main()` only prints status lines and carries a TODO outlining the intended steps. The pieces such a runner would depend on are also missing — the curated benchmark portfolios under `tests/fixtures/sample_profiles/` do not yet exist, a generation-side mock LLM is not provided (only a mock *embedding* provider is), and no `eval_results.json` report is produced even though the existing `.github/workflows/eval.yml` CI job already tries to publish one on pull requests. This work sits squarely in the RAG evaluation area of the codebase (retriever → generator → evaluator). A successful eventual solution would run representative portfolios through that pipeline with a deterministic mock LLM and persist a machine-readable JSON report of quality scores, making review quality measurable and comparable across changes without depending on live API requests or external services.

**Branch name:** `feat/40-offline-eval-runner`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" selection reasoning

**Skill alignment.** The issue is a strong match for my background. It is a standalone Python deliverable (a script under `scripts/`), and my strengths — Python, RAG pipelines, retrieval, and LLM-based applications — map directly onto its core: loading fixtures, wiring a retriever + generator + evaluator, and serializing scores to JSON. I have built RAG pipelines before, so the retriever → generator → evaluator shape here is familiar, and my FastAPI/Docker/PostgreSQL experience helps me reason about how the offline runner must stay decoupled from the request path and the database. JSON serialization and pytest-style mocking are routine for me, which matters because the runner's output contract and its determinism both hinge on those skills.

**Why Tier 3 makes it challenging.** This is not a localized bug fix. The eval "suite" that exists (`EvalSuite`) only scores *one* query's chunks and feedback; it does not run a pipeline. So the runner has to assemble the "full RAG pipeline" itself — embedding, hybrid retrieval, LLM generation, then scoring — over a *set* of portfolios, which touches at least half a dozen modules across `rag/`, `ingestion/`, and `scripts/`. The two files named in the issue (`scripts/run_evals.py`, `rag/evaluator/eval_suite.py`) are just the visible surface; the real work is integration and determinism.

**Expected dependencies and hidden scope.** Concretely, the runner will likely need: `MockEmbeddingProvider` (exists, deterministic), the `HybridRetriever`/`VectorStore` (ChromaDB-backed) + `KeywordSearcher` (BM25), `ReviewGenerator`, and `EvalSuite`. Hidden scope I identified while reading the code: (1) there is **no** deterministic mock LLM for *generation* — only for embeddings — so one must be introduced or the OpenAI client stubbed; (2) the benchmark portfolio fixtures **do not exist** and must be authored, and there is no established golden/expected-output format yet; (3) the TODO in `run_evals.py` lists an **actionability** score that `EvalSuite` does not implement (it computes only relevance + faithfulness), so "actionability" is either out of scope or a small new metric to define; (4) `core/services/review_service.py` currently runs the review pipeline with **stubbed** logic and never actually invokes `EvalSuite`, so "the eval suite runs inline during API requests" describes design intent more than current runtime behavior — the runner cannot simply lift existing wiring, it has to create it.

**Main risks.** External APIs (real OpenAI/OpenRouter calls) must be avoided so results are deterministic and CI-safe — the `.github/workflows/eval.yml` job runs with `LLM_PROVIDER=mock` and **no** database or Docker services, so the runner must work fully offline. ChromaDB is a Python dependency and can run embedded/ephemeral, but I need to confirm the runner never requires the Postgres/Redis/vector-db containers. Benchmark-schema ambiguity (what a "portfolio" fixture must contain, and what thresholds define acceptable quality) is the biggest open question and will need clarification in Week 8. Finally, `eval_results.json` is not currently git-ignored, so I'll need to decide whether it is a committed artifact or a generated one.

**How the work can be bounded.** I will keep the scope to: (a) a curated set of benchmark portfolio fixtures, (b) a standalone runner that executes the real retrieval + generation + scoring path with a deterministic mock LLM, (c) a machine-readable JSON report matching the contract `eval.yml` expects, and (d) focused tests. I will explicitly avoid refactoring `review_service.py`, changing the API, or wiring evaluation back into the request path — those are separate concerns.

**Final decision.** I'm proceeding with issue #40. It is ambitious for a Tier 3 — the integration and determinism work is real and the fixtures/mock-LLM/actionability gaps mean it is clearly not a beginner task — but it is well within reach given my RAG and Python background, and the scope can be bounded cleanly to an offline, CI-friendly runner without touching production request paths.

---

### Codebase orientation notes

Most relevant files for issue #40 (all read during this Week 7 orientation):

| File | Responsibility | Why it matters to #40 |
|---|---|---|
| [scripts/run_evals.py](scripts/run_evals.py) | The eval-runner entry point (currently a stub `main()` with a TODO). | This is the primary file to implement — it must load benchmark portfolios, drive the pipeline, and write `eval_results.json`. |
| [rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py) | `EvalSuite.run(query, chunks, feedback)` → `EvalResult(relevance, faithfulness, overall)`. | The scoring engine the runner will call per portfolio; defines the current score shape (no actionability yet). |
| [rag/evaluator/relevance_scorer.py](rag/evaluator/relevance_scorer.py) | Deterministic keyword-overlap relevance score (0–1). | Confirms scoring needs no LLM and is reproducible — good for a deterministic report. |
| [rag/evaluator/faithfulness_checker.py](rag/evaluator/faithfulness_checker.py) | Deterministic claim-vs-context overlap faithfulness score (0–1). | Same determinism guarantee; the runner can rely on stable scores. |
| [rag/generator/review_generator.py](rag/generator/review_generator.py) | `ReviewGenerator` produces feedback sections via a live `openai.OpenAI` client. | The generation step the runner must exercise — and the reason a mock/injected LLM is required for offline runs. |
| [rag/retriever/hybrid.py](rag/retriever/hybrid.py) | `HybridRetriever.retrieve(...)` combines `VectorStore` (Chroma) + `KeywordSearcher` (BM25). | The retrieval half of the "full RAG pipeline" the runner must assemble. |
| [ingestion/embeddings/provider.py](ingestion/embeddings/provider.py) | `MockEmbeddingProvider` (deterministic, seeded) + `get_embedding_provider("mock"\|"openai")` factory. | Provides the deterministic embedding path the offline runner should use. |
| [core/services/review_service.py](core/services/review_service.py) | `process_review()` orchestrates the request-time pipeline — but its steps are stubs returning hardcoded data. | Shows the *intended* pipeline shape and that `EvalSuite` is not actually wired into requests today. |
| [.github/workflows/eval.yml](.github/workflows/eval.yml) | CI job that runs `python scripts/run_evals.py` with `LLM_PROVIDER=mock` and comments `eval_results.json` on PRs. | Defines the runner's real contract: honor `LLM_PROVIDER=mock`, emit `eval_results.json`, run with no DB/services. |
| [core/config.py](core/config.py) | `Settings` with `llm_provider` (default `"mock"`) and provider/API settings. | The env-var switch (`LLM_PROVIDER`) the runner should read to select mock vs. real generation. |

**Where the current "inline" evaluation sits in the review pipeline.** A review request flows `POST /reviews` ([api/routes/reviews.py](api/routes/reviews.py)) → `create_review()` (persists a `pending` row) → a FastAPI background task runs `process_review()` in [core/services/review_service.py](core/services/review_service.py), whose intended order is ingestion → agent orchestration → RAG retrieval + generation → safety checks → persist sections + `overall_score`. In the code as it stands, those inner steps return hardcoded stub output and `EvalSuite` is never invoked, so quality scoring is effectively *designed for* the request path but not exercised there. The offline runner for #40 would sidestep that request path entirely: instead of the stubbed service, it would load benchmark portfolios, run them through the real embedding → `HybridRetriever` → `ReviewGenerator` → `EvalSuite` chain with a deterministic mock LLM, and write the aggregated scores to `eval_results.json`.

---

### Local setup verification (Week 7)

Verified this session on macOS (Apple Silicon / arm64). Docker has since been installed, so the previously blocked local setup was completed and both endpoints were confirmed responding.

| Tool | Required (docs/SETUP.md) | Installed / used | Status |
|---|---|---|---|
| Git | 2.39+ | 2.50.1 | OK |
| Python (project `.venv`) | 3.11+ | 3.14.0 | OK — all dependencies installed and the app runs on 3.14 |
| Node.js | 18+ | 22.17.1 | OK |
| npm | 9+ | 10.9.2 | OK |
| Docker | 24+ | 29.6.1 | OK |
| Docker Compose | 2.20+ | v5.3.0 | OK |
| make | — | GNU Make 3.81 | OK |

- **Docker services (`docker compose up -d`):** `db` (PostgreSQL, healthy) and `redis` (healthy) — the services `make setup`/`make run` actually need. `vector-db` (ChromaDB) is a known non-blocker (see warnings).
- **`make setup`:** succeeded — created the `.venv`, installed the Python dependencies, ran `alembic upgrade head`, and seeded the database. The only hiccup was the final `npm install` hitting a pre-existing permission problem in the global npm cache (`~/.npm`); it completed after pointing npm at a clean cache directory. No tracked project files were changed to make setup work.
- **`make run`:** succeeded — `uvicorn api.main:app` reached "Application startup complete" (connected to PostgreSQL) and the Vite dev server started.
- **Frontend:** `http://localhost:5173` → HTTP **200**, serving the PathReview Vite/React app (`<title>PathReview - AI Portfolio Review Assistant</title>`).
- **API docs:** `http://localhost:8000/docs` → HTTP **200**, FastAPI Swagger UI for the PathReview API; `/openapi.json` loads with 9 routes.
- **`.env`:** present and git-ignored; no secret values were read, printed, or committed. `LLM_PROVIDER=mock`, so no real API key is required.
- **Non-blocking warnings:** (1) the `vector-db` (ChromaDB `0.4.22`) container exits at startup with `AttributeError: np.float_ was removed in the NumPy 2.0 release` — an incompatibility inside that pinned image; it is not required for `make setup`, `make run`, the frontend, or the API docs, all of which succeed without it, so no Docker-config change was made. (2) The global npm cache permission issue noted above (worked around, not a project defect). (3) `docker-compose.yml` emits an "obsolete `version` attribute" notice — cosmetic only.

Scope note: this confirms local setup and endpoint availability only — it does not exercise the full review-generation flow, and no issue #40 work was started.
