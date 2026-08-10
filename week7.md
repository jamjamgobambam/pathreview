# PathReview Issue #40 — Week 7 Handoff

## 1. Purpose of this document

Week 7 covered **issue selection, repository orientation, Git configuration, local environment setup, and documentation** for GitHub issue #40. **Issue implementation has not begun** — no runner logic, benchmark fixtures, mock LLM, or tests for #40 exist on the branch.

This file is an engineering handoff written for a future Week 8 Claude Code session that has **no conversational memory** of Week 7. It captures verified repository facts, the runtime discovery that matters most for this issue, the setup outcome, and the open questions, so the next session can continue without asking the user to restate history.

**The next session must still verify the current repository state before acting** — treat every "current state" claim here as true *as of the Week 7 commits* and re-check it (branch, clean tree, issue text, service state) rather than assuming it is unchanged.

## 2. Repository and Git state

| Item | Value |
|---|---|
| Local repo path | `/Users/pramodkrishnachari/PRAMOD/PERSONAL/CodePath/Projects/PathReview` |
| Fork (`origin`) | `https://github.com/ChariPramod/pathreview-pramod.git` |
| Upstream (`upstream`) | `https://github.com/ascherj/pathreview.git` |
| Working branch | `feat/40-offline-eval-runner` |
| Branch submission URL | `https://github.com/ChariPramod/pathreview-pramod/tree/feat/40-offline-eval-runner` |
| HEAD at handoff | `eecdcc86de85969a1045b388bac5e47e45235ade` |
| Working tree at handoff | Clean (only the two Week 7 doc commits + this handoff) |
| Pull request | **None opened** |
| Issue implementation | **Not started** |

**Week 7 commit history (branch `feat/40-offline-eval-runner`):**

- `0f50a70c0e7fa9c4412269c29f3f0384e0bc92ae` — `docs(rag): add Week 7 issue selection journal`
- `eecdcc86de85969a1045b388bac5e47e45235ade` — `docs(rag): confirm Week 7 local setup`

`main` and `origin/main` are at `54cc749`. Local `main` was intentionally **not** fast-forwarded to `upstream/main`, which was 2 trivial commits ahead at Week 7 (a setup-URL fix + a merge). Remotes were reconfigured in Week 7: the original clone had `origin` pointing at the upstream `ascherj/pathreview`; it was renamed to `upstream` and the fork added as `origin` (non-destructively).

## 3. Selected issue

| Field | Value |
|---|---|
| Number | 40 |
| Title | `Implement an offline eval runner that measures review quality across a benchmark portfolio set` |
| URL | `https://github.com/ascherj/pathreview/issues/40` |
| Tier | Tier 3 |
| Labels | `tier-3`, `rag`, `tests`, `devops`, `enhancement` |
| Estimated effort | 7–10 hours |
| Files named in issue | `scripts/run_evals.py`, `rag/evaluator/eval_suite.py` |

**Problem statement (issue body, original wording):** "The current eval suite runs inline during API requests. Add a standalone eval runner (`scripts/run_evals.py`) that tests the full RAG pipeline against a curated set of benchmark portfolios and outputs a JSON report of quality scores."

**What a successful eventual implementation should accomplish:** a standalone, offline command that loads a curated set of benchmark portfolios, runs them through the real retrieval + generation + scoring path using a deterministic (non-networked) LLM, and writes a machine-readable `eval_results.json` of quality scores — reproducibly and without live API calls or external services, so review quality can be measured across changes.

**Explicitly outside the intended scope:** wiring evaluation into the request-time path, changing API behavior, refactoring `core/services/review_service.py`, or any unrelated refactor.

**Claim status:** the user has already commented on the issue — *"I would like to work on this issue."* **Do not post another claim comment.** Claims are **non-exclusive**; other students (`christophermayfield`, `ItachiSusie`) also commented, which the course allows and is not a reason to abandon the issue.

## 4. Why this issue was selected

Preserved from `JOURNAL.md`'s "Is this right for me?" reasoning (student background: strong Python; prior RAG-pipeline experience; retrieval, OpenSearch, PostgreSQL, Airflow, and LLM-application experience; FastAPI + Docker; comfortable with JSON serialization and pytest-style mocking):

- **Alignment.** The deliverable is a standalone Python script that assembles a retriever + generator + evaluator and serializes scores to JSON — directly matching the student's RAG and Python strengths. FastAPI/Docker/PostgreSQL experience helps reason about keeping the runner decoupled from the request path and the database.
- **Why Tier 3 is genuinely challenging.** The existing `EvalSuite` only scores *one* query's chunks/feedback; it does not run a pipeline. The runner must assemble the full embedding → retrieval → generation → scoring path over a *set* of portfolios, touching several modules across `rag/`, `ingestion/`, and `scripts/`. The two files named in the issue are the visible surface; the real work is integration + determinism, plus authoring fixtures and deciding a mock-generation strategy.
- **Why it is still manageable.** Scoring is already deterministic and lexical; embeddings have a deterministic mock; the CI contract is known. The scope can be bounded to an offline, CI-safe runner.
- **How to bound the future implementation.** (a) curated benchmark fixtures, (b) a standalone runner exercising the real retrieval + generation + scoring with a deterministic mock LLM, (c) a JSON report matching what CI expects, (d) focused tests — while avoiding request-path/API changes.

## 5. PathReview architecture (verified)

Multi-service FastAPI (Python 3.11+ target) + React/Vite app. Documented flow (`docs/ARCHITECTURE.md`): API → Ingestion → Agent → RAG (hybrid retrieval + LLM generation + evaluate) → Safety → Review Output.

| Subsystem | Primary responsibility | Important entry points | Interaction |
|---|---|---|---|
| `api/` | FastAPI REST layer: auth (JWT), validation (Pydantic), routing | `api/main.py` (`app`), `api/routes/{reviews,profiles,auth,health}.py`, `api/schemas/` | Routes delegate to `core/services/` |
| `core/` | Config, DB, models, service layer | `core/config.py` (`Settings`), `core/database.py`, `core/models/`, `core/services/{review_service,profile_service}.py` | Called by API; talks to Postgres via SQLAlchemy async |
| `ingestion/` | Parse → chunk → embed → store | `ingestion/pipeline.py`, `ingestion/parsers/`, `ingestion/chunking/`, `ingestion/embeddings/provider.py` | Produces chunks/embeddings consumed by `rag/` |
| `rag/` | Hybrid retrieval, LLM generation, quality evaluation | `rag/retriever/`, `rag/generator/`, `rag/evaluator/` | Core of issue #40 |
| `agent/` | Plan-execute multi-tool orchestration | `agent/orchestrator.py`, `agent/tools/` | Analysis tools feeding review |
| `safety/` | Bias/content/PII/prompt-injection guards | `safety/{bias_detector,content_filter,pii_scrubber,prompt_defense}.py` | Wraps generation output |
| `frontend/` | React + TypeScript + Vite dashboard | `frontend/src/main.tsx`, `frontend/package.json` | Calls the API |
| `tests/` | pytest suite (markers: `unit`, `integration`, `benchmark`, `security`) | `tests/unit/`, `tests/conftest.py`, `tests/benchmarks/` (only `__init__.py`) | Isolates via mocks |
| `scripts/` | Ops scripts | `scripts/run_evals.py`, `scripts/seed_db.py`, `scripts/seed_issues.py` | `run_evals.py` is the #40 target |

**Verified portfolio-review request flow:** `POST /reviews` ([api/routes/reviews.py:22](api/routes/reviews.py#L22)) → `create_review()` persists a `pending` `Review` → a FastAPI `BackgroundTasks` job runs `process_review()` ([core/services/review_service.py:82](core/services/review_service.py#L82)) whose intended order is ingestion → agent → RAG retrieval+generation → safety → persist sections + `overall_score`. **See §8 for the critical caveat: those inner steps are stubs.**

## 6. Issue-specific codebase map (verified symbols)

| File | Important symbols | Responsibility | Relevance to #40 |
|---|---|---|---|
| `scripts/run_evals.py` | `main()` | Scaffold only: prints two status lines and an inline comment listing four intended steps (load benchmark portfolios from `tests/fixtures/sample_profiles/`; run each through the full RAG pipeline with a mock LLM; score relevance, faithfulness, and actionability; output `eval_results.json`). | **Primary file to implement.** |
| `rag/evaluator/eval_suite.py` | `EvalSuite`, `EvalSuite.run(query: str, chunks: list[dict], feedback: str) -> EvalResult`; `EvalResult(relevance_score, faithfulness_score, overall_score: float)` | Runs the two scorers; `overall = (relevance + faithfulness) / 2`. | The scoring engine the runner calls per portfolio. |
| `rag/evaluator/relevance_scorer.py` | `RelevanceScorer.score(query, chunks) -> float` | Deterministic keyword-overlap ratio (query tokens ∩ chunk tokens). No LLM. | Deterministic, CI-safe scoring. |
| `rag/evaluator/faithfulness_checker.py` | `FaithfulnessChecker.check(feedback, context_chunks) -> float` | Deterministic: splits feedback into sentence "claims", counts those with ≥2 non-stopword overlaps with context. | Deterministic, CI-safe scoring. |
| `rag/generator/review_generator.py` | `ReviewConfig`, `ReviewGenerator.__init__` (builds `openai.OpenAI(...)`), `generate_section(...)`, `generate_full_review(profile_data, retrieved_chunks) -> list[FeedbackSection]` | LLM generation across 5 sections (`skills_feedback`, `projects_feedback`, `presentation_feedback`, `gaps_feedback`, `first_impression`). | **Non-deterministic/networked** — the reason a mock-generation strategy is central. |
| `rag/retriever/hybrid.py` | `HybridRetriever(vector_store, keyword_searcher, ...)`, `.retrieve(query, profile_id, query_embedding, ...)` | Combines vector + keyword retrieval. | Retrieval half of the pipeline. |
| `rag/retriever/vector_store.py` | `VectorStore(persist_dir=".chromadb")`, `chromadb.PersistentClient(path=persist_dir)`, `add_chunks`, `query` | **Embedded** Chroma (local dir) — *not* the HTTP service on 8001. | Suggests the runner can use embedded/ephemeral Chroma (see §10, §17 Q5). |
| `rag/retriever/keyword_search.py` | `KeywordSearcher.index(chunks)`, `.search(query, top_k=10)` | BM25 (`rank-bm25`). | Keyword retrieval. |
| `ingestion/embeddings/provider.py` | `EmbeddingProvider` (ABC), `MockEmbeddingProvider` (`EMBEDDING_DIM=1536`, SHA256-seeded), `OpenAIEmbeddingProvider`, `get_embedding_provider("mock"\|"openai")` | Deterministic mock embeddings + factory. | The deterministic embedding path for the runner. |
| `core/services/review_service.py` | `create_review`, `process_review`, `_run_rag_retrieval_generation`, `_run_safety_checks` | Orchestrates the request-time pipeline — steps are stubs (see §8). | Shows intended shape; confirms `EvalSuite` is not wired into requests. |
| `core/config.py` | `Settings.llm_provider="mock"` (default), `openrouter_model="google/gemma-3-27b-it:free"`, `max_chunks_per_query=10`, `min_relevance_score=0.3`, `vector_db_url`, DB/Redis URLs | Env-driven config; `LLM_PROVIDER` env var selects mock vs real. | The switch the runner should honor. |
| `.github/workflows/eval.yml` | job `eval` | On PRs touching `rag/**`, `ingestion/chunking/**`, `ingestion/embeddings/**`: `pip install -e ".[dev]"` → `python scripts/run_evals.py` (env `LLM_PROVIDER: mock`) → read `eval_results.json` → comment on PR. **No DB/services started.** | Defines the runner's hard contract (see §11). |

## 7. Current evaluator behavior (verified)

- `EvalSuite.run()` takes **one** `query: str`, a list of retrieved `chunks: list[dict]`, and generated `feedback: str`.
- It returns an `EvalResult` with `relevance_score`, `faithfulness_score`, and `overall_score` (floats).
- `overall_score` is computed **only** from the two implemented metrics: `(relevance + faithfulness) / 2`.
- `EvalSuite` is a **scorer for a single result, not a benchmark runner** — it neither loads portfolios nor executes retrieval/generation.
- `scripts/run_evals.py` is a **stub** (`main()` prints and lists intended steps; no logic).
- **`tests/fixtures/sample_profiles/` does not exist** (there is no `tests/fixtures/` directory at all; `tests/benchmarks/` contains only `__init__.py`). *Verify again in Week 8.*
- **No `eval_results.json` is produced** by the current code. *Verify again.*
- **Actionability** is named only in the `scripts/run_evals.py` intended-steps comment; it is **not implemented** in `EvalSuite` (or anywhere in `rag/`). *Verify again.*

## 8. Important runtime reality discovered in Week 7

**The issue's premise and the current code diverge — this is the single most important handoff fact.**

- The issue says evaluation "currently runs inline during API requests."
- In the current repository, **`EvalSuite` is never invoked by the runtime review path.** A code search found no runtime callers — only its own definition and the unit tests that import the individual scorers.
- `core/services/review_service.py`'s `process_review()` inner steps (`_run_ingestion_pipeline`, `_run_agent_orchestration`, `_run_rag_retrieval_generation`, `_run_safety_checks`) return **hardcoded stub data** (the source explicitly marks them as not-yet-implemented). They do not call the real `ReviewGenerator`, `HybridRetriever`, or `EvalSuite`.
- Therefore the offline runner **cannot lift already-working request-time wiring** — there is none to lift. It will need to assemble/introduce an explicit offline pipeline from the real `rag/`/`ingestion/` components.

Distinguish clearly:
- **Design intent** (`docs/ARCHITECTURE.md`): RAG "retrieve context, generate feedback, evaluate."
- **Current implemented behavior**: request path is stubbed; evaluator is standalone and uncalled.
- **Issue requirement**: a *separate offline* runner over benchmark portfolios producing JSON — which sidesteps the request path entirely.

## 9. Expected future offline evaluation flow (proposed — not an approved design)

A likely conceptual path for Week 8 to investigate (do **not** treat as final):

1. Load benchmark portfolio fixtures.
2. Convert each benchmark into retrievable document chunks.
3. Generate deterministic embeddings (`MockEmbeddingProvider`).
4. Index/prepare retrieval state (embedded or ephemeral vector store + BM25 index).
5. Execute hybrid retrieval for benchmark queries.
6. Generate review feedback via a **deterministic mock LLM**.
7. Score retrieval relevance (`RelevanceScorer`).
8. Score generation faithfulness (`FaithfulnessChecker`).
9. Resolve whether actionability is required (see §17 Q3).
10. Aggregate per-benchmark and portfolio-wide results.
11. Write `eval_results.json`.
12. Ensure it runs under `.github/workflows/eval.yml` with **no external services or API calls**.

*This is a proposed Week 8 investigation direction, not an approved final design.*

## 10. Deterministic vs non-deterministic / external components (verified)

**Deterministic (safe for offline/CI):**
- `MockEmbeddingProvider` — SHA256-seeded, 1536-dim, normalized; same input → same vector.
- `RelevanceScorer.score` — lexical keyword overlap; no randomness.
- `FaithfulnessChecker.check` — lexical claim/context overlap; no randomness.
- `VectorStore` — embedded `chromadb.PersistentClient` (local dir), no network.
- `KeywordSearcher` — BM25 over in-memory chunks.

**Non-deterministic / external (must be avoided or replaced in the runner):**
- `ReviewGenerator` — constructs a live `openai.OpenAI` client and calls chat completions (real OpenAI/OpenRouter). Networked and non-deterministic.
- Any real API key path (`OPENAI_API_KEY` / `openrouter_*` in `core/config.py`).
- The Docker `vector-db` (Chroma HTTP) service — but note the app's `VectorStore` uses **embedded** Chroma, so this container may be unnecessary for the runner.

**A deterministic generation strategy is one of the central Week 8 design questions** (there is no mock *generation* LLM today — only a mock embedding provider).

## 11. CI contract (`.github/workflows/eval.yml`)

- **Trigger:** `pull_request` touching `rag/**`, `ingestion/chunking/**`, `ingestion/embeddings/**`.
- **Setup:** `actions/setup-python@v5` (Python 3.11) → `pip install -e ".[dev]"`.
- **Run command:** `python scripts/run_evals.py` with environment variable `LLM_PROVIDER: mock`.
- **Services:** **none** — no Docker/Postgres/Redis/Chroma are started in the workflow.
- **Artifact/behavior:** the job reads `eval_results.json` from the repo root and posts its contents as a PR comment (`## RAG Evaluation Results`). If the file is missing it comments "Eval results not found."
- **Constraints this imposes:** the runner must (a) honor `LLM_PROVIDER=mock`, (b) run to completion with **no external services and no network/API calls**, (c) write `eval_results.json` to the repo root, on Python 3.11.

## 12. Test and fixture findings (verified)

Verified facts:
- **Evaluator tests:** `tests/unit/test_relevance_scorer.py`, `tests/unit/test_faithfulness_checker.py` (import the scorers directly). **There is no test for `EvalSuite` itself, and no test for `scripts/run_evals.py`.**
- **RAG/related tests:** `test_output_parser.py`, `test_prompt_templates.py`, `test_llm_provider_contract.py` (the "LLM provider contract" test is actually about the **embedding** providers), `test_keyword_search.py`, `test_review_service.py` (covers `create_review`/`get_review`/`list_reviews` only — **not** `process_review`).
- **Conventions:** pytest with markers `@pytest.mark.unit` / `@pytest.mark.asyncio`; `unittest.mock` (`AsyncMock`, `Mock`, `patch`); async DB sessions mocked via `AsyncMock`. `tests/conftest.py` provides small `sample_resume_text` / `sample_readme_text` fixtures only.
- **`tests/fixtures/sample_profiles/`:** does **not** exist. No benchmark schema, golden outputs, or score thresholds exist anywhere.

Future recommendations (not yet done): a unit test for the runner (with mock LLM + tiny fixture), a test asserting the `eval_results.json` schema, and determinism tests (same input → identical scores).

## 13. Local environment verification (final Week 7 state)

Environment: **macOS, Apple Silicon / arm64.**

| Tool | Version |
|---|---|
| Git | 2.50.1 |
| Python (project `.venv`) | 3.14.0 |
| Node.js | 22.17.1 |
| npm | 10.9.2 |
| Docker | 29.6.1 |
| Docker Compose | v5.3.0 |
| GNU Make | 3.81 |

Verified outcomes:
- `make setup` **succeeded**. Python dependencies installed successfully **on Python 3.14** (no Python 3.11 fallback was needed, though Homebrew `python3.11` is available at `/opt/homebrew/bin/python3.11` if a future issue requires it).
- Alembic migrations completed (`alembic upgrade head`).
- The database was seeded (`scripts/seed_db.py`; sample users `user1@example.com` … `user3@example.com`).
- `make run` **succeeded** (uvicorn reached "Application startup complete", Postgres-connected; Vite dev server started).
- Frontend: `http://localhost:5173` → **HTTP 200** (PathReview Vite/React app).
- API docs: `http://localhost:8000/docs` → **HTTP 200** (FastAPI Swagger, "PathReview API").
- `http://localhost:8000/openapi.json` loaded with **9 routes** (`/`, `/health`, `/auth/login`, `/auth/register`, `/profiles`, `/profiles/{profile_id}`, `/reviews`, `/reviews/{review_id}`, `/reviews/{review_id}/status`).
- In `JOURNAL.md`, both the **Setup confirmation** and **Cohort ledger** checkboxes are checked.

(No API keys, `.env` contents, tokens, or credentials are recorded here. `.env` is git-ignored; `LLM_PROVIDER=mock`, so no real key is required to run.)

## 14. Setup issues and workarounds

### npm cache permission issue
- The global npm cache under `~/.npm` had a **pre-existing** permission problem (`EACCES: permission denied, mkdir '~/.npm/_cacache/...'`) that failed the final `npm install` step of `make setup`.
- **Resolution:** direct npm at a fresh, writable cache directory and rerun the frontend install — no `sudo`, no tracked-file changes. Reproducible form:
  ```bash
  cd frontend && npm install --cache "$(mktemp -d)"
  ```
  (In Week 7 this was done by setting `npm_config_cache` to a clean scratch directory before `npm install`.)
- `npm install` also produced incidental churn in the tracked `frontend/package-lock.json` (removal of some `"peer": true` lines); this was **restored** (`git restore frontend/package-lock.json`) rather than committed, keeping the diff limited to docs.

### ChromaDB container issue
- `pathreview-vector-db-1` (image `chromadb/chroma:0.4.22`) **exited during startup** with `AttributeError: np.float_ was removed in the NumPy 2.0 release. Use np.float64 instead.` — an incompatibility baked into that pinned image.
- PostgreSQL (`pathreview-db-1`) and Redis (`pathreview-redis-1`) remained **healthy**.
- `make setup`, `make run`, the frontend, and the API docs all **succeeded without** the vector-db container.
- `docker-compose.yml` was **intentionally not modified** (out of Week 7 scope, and it is a tracked Docker-config file).
- **Week 8 relevance:** likely a non-issue, because the app's `VectorStore` uses **embedded** Chroma (`PersistentClient`), not the HTTP container. It only becomes relevant if the runner is designed to depend on the external Chroma service — which it should probably avoid (§17 Q5).

## 15. Current process and service state (verify before trusting)

- The `make run` processes started for verification were **stopped**; ports **5173** and **8000** were **free** afterward, with no orphaned uvicorn/vite processes.
- PostgreSQL and Redis containers were **left running**; the database remained seeded.
- The next session can start the app again with `make run` (with `docker` available on PATH).
- **The next session must verify this state** (`docker compose ps`, port checks) rather than assuming it is unchanged — containers may have been stopped, and Docker's CLI may need PATH help (see §20).

## 16. Decisions already made (scope guardrails)

- Remain on `feat/40-offline-eval-runner`.
- Do **not** implement unrelated changes in `core/services/review_service.py`.
- Do **not** change API behavior.
- Do **not** wire evaluation into request-time processing unless the issue explicitly requires it.
- Avoid **live LLM calls** in the eval runner; keep execution deterministic and CI-safe.
- Do **not** assume actionability scoring is required until the issue text and repository evidence are reconciled.
- Do **not** modify Docker configuration solely to fix the Week 7 Chroma problem.
- Keep `eval_results.json` handling consistent with the CI workflow's expectations (repo-root file, read after the run).
- Follow **Conventional Commits** (`docs/CONTRIBUTING.md`: types `fix|feat|test|docs|refactor|perf|chore|ci`; scopes include `rag`, `ingestion`, `api`).
- Add/update relevant tests for all implementation changes; run `make check` (ruff + black + mypy) and `make test-unit` before any future PR.

## 17. Open questions for Week 8

1. What exact **benchmark portfolio schema** should be used (fields, format, location)?
2. How many benchmark portfolios and queries are sufficient to be representative yet fast in CI?
3. Does the issue require an **actionability** score, or only the relevance + faithfulness that `EvalSuite` already supports?
4. Should a **mock LLM provider** be added as a reusable project abstraction (mirroring `get_embedding_provider`), or should the runner inject a local deterministic generator?
5. Can the runner use an **embedded/ephemeral vector store** (the code already uses embedded Chroma) instead of the Docker Chroma service?
6. Must the runner execute **every** production RAG component, or is a deterministic equivalent acceptable for CI?
7. What should the **`eval_results.json` schema** be (per-portfolio entries, aggregate scores, metadata)?
8. Should `eval_results.json` be **git-ignored, committed, or generated only in CI**? (It is currently **not** in `.gitignore`.)
9. What **minimum score thresholds** define success/failure?
10. Should the command **exit non-zero** when scores fall below thresholds (to gate CI)?
11. Which **existing test patterns** should the new tests follow (unit markers, mock style)?
12. Is **clarification from the issue maintainer** needed before implementation (given the request-path discrepancy in §8)?
13. How should the runner reconcile that `EvalSuite.run` expects a single `query` while a "portfolio" implies multiple queries/sections?

## 18. Risks for Week 8

- Accidentally using **live APIs** (real OpenAI/OpenRouter) — breaks determinism and CI.
- **Nondeterministic generation** producing unstable scores.
- Depending on **unavailable Docker services** (e.g., the crashing Chroma container).
- **Over-expanding** the issue into production review-orchestration work in `review_service.py`.
- **Inventing a benchmark format** without evidence or maintainer input.
- Adding an **actionability metric** without agreement that it is in scope.
- Producing a **JSON format incompatible** with the `eval.yml` consumer.
- **Modifying unrelated modules** (API, request path, Docker config).
- Writing **tests that don't match** repository patterns.
- Treating the **issue description as more accurate than the current code** without reconciling the §8 discrepancy.

## 19. Week 8 starting checklist

1. Verify branch is `feat/40-offline-eval-runner` and the working tree is clean.
2. `git fetch origin --prune` and `git fetch upstream --prune` — **without** rewriting history (no reset/rebase/force).
3. Confirm issue #40's text, labels, and comments have not materially changed.
4. Re-read `week7.md`, `JOURNAL.md`, and the relevant source files (§6).
5. Verify Docker/service state (`docker compose ps`) and restart services if needed.
6. **Reproduce the missing behavior** (run `python scripts/run_evals.py` and confirm it is still a stub producing no report).
7. Write a **structured markdown implementation plan** before changing any source.
8. Identify the **smallest viable benchmark schema**.
9. Decide and document the **deterministic LLM approach**.
10. Resolve the **actionability ambiguity** (§17 Q3).
11. Define the **`eval_results.json` contract**.
12. Identify the **exact tests** to add.
13. **Do not implement until the plan is reviewed.**

**Likely Week 8 course deliverables:** issue-reproduction evidence; a structured markdown solution plan; at least two starter commits where required; a short Loom walkthrough if the assignment requires it; **no PR until the implementation phase is complete.**

## 20. Commands likely needed at the start of Week 8

```bash
cd /Users/pramodkrishnachari/PRAMOD/PERSONAL/CodePath/Projects/PathReview

git status
git branch --show-current
git remote -v
git fetch origin --prune
git fetch upstream --prune

docker compose ps
make run
```

Safe endpoint verification:

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:5173
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs
```

Note: on this machine the `docker` CLI was not on the default non-interactive shell PATH in Week 7. Docker Desktop's binaries live at `/Applications/Docker.app/Contents/Resources/bin`; prepend that to `PATH` if `docker` is not found. Do not run destructive commands (no `docker compose down -v`, no volume deletion, no `git reset --hard`, no force-push).

## 21. Week 7 completion status

### Completed
- Issue #40 selected and claimed (existing comment; no duplicate).
- Cohort ledger completed (user-confirmed).
- Branch `feat/40-offline-eval-runner` created and pushed.
- Repository and issue-specific codebase investigated and verified.
- `JOURNAL.md` completed (issue selection, reasoning, codebase map, setup record).
- Docker installed; local setup completed on Python 3.14.
- Frontend and API verified (both HTTP 200); OpenAPI has 9 routes.
- Both Week 7 commits pushed to the fork (`0f50a70`, `eecdcc8`).

### Not started
- Issue reproduction for Week 8.
- Formal solution plan.
- Benchmark fixture design.
- Mock LLM implementation.
- Offline eval runner implementation.
- Tests for issue #40.
- Pull request.

### External action
- Course-portal submission of the branch URL (`https://github.com/ChariPramod/pathreview-pramod/tree/feat/40-offline-eval-runner`), unless already completed.

---

Week 7 is complete. Issue #40 implementation has not started. Read this file before beginning Week 8.
