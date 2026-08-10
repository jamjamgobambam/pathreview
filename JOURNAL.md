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

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ChariPramod/pathreview-pramod/commit/5a0d25b16476fa556716e3de758dba1555634758

**Reproduction summary:**
Running `LLM_PROVIDER=mock python scripts/run_evals.py` exits 0 and prints "Results written to eval_results.json", but writes no file and changes nothing—the message is unconditional and `main()` is a TODO comment. Because the CI job swallows the resulting read error, every pull request touching `rag/**` gets a green check alongside an "Eval results not found" comment, so a passing evaluation is indistinguishable from one that never ran.

**PLAN.md link:** https://github.com/ChariPramod/pathreview-pramod/blob/feat/40-offline-eval-runner/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
No implementation blockers remain. Open scope questions include whether actionability scoring is required, whether score thresholds should fail CI, the expected benchmark and report schemas, and whether `eval_results.json` should be committed or treated as a generated artifact.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All six PLAN.md steps are implemented and committed. Step 2 (repair the `Chunk` → `VectorStore` seam) landed first because nothing downstream composes without it: [`f3d6918`](https://github.com/ChariPramod/pathreview-pramod/commit/f3d6918f5126f89b1d763eec4d57b9b9a7f90cc3) makes `VectorStore.add_chunks` read `source_id`/`chunk_index` from `chunk.metadata` and derive ids as `{source_id}_chunk_{chunk_index}`, matching the convention `BatchEmbeddingProcessor._store_embedding` already writes. Step 1 followed in [`c0a9db4`](https://github.com/ChariPramod/pathreview-pramod/commit/c0a9db4a1db1caa795258a624085d595ada0f7cb): `MockReviewGenerator` plus `get_review_generator()`, which is the first code in the repository to read `settings.llm_provider` for generation. Step 3 added four benchmark portfolios in [`7fd944c`](https://github.com/ChariPramod/pathreview-pramod/commit/7fd944c42749a45eedf1c2a1ec44be487d31bf26). Steps 4 and 5 landed as [`a58f625`](https://github.com/ChariPramod/pathreview-pramod/commit/a58f6259132268ff805970e61334aa356c652bee) (`rag/evaluator/benchmark_runner.py`, the composition seam) and [`769409e`](https://github.com/ChariPramod/pathreview-pramod/commit/769409e9e98ef4fa423131ffb2cb3a7bcffae878) (`scripts/run_evals.py` as a thin CLI).

What works now: `LLM_PROVIDER=mock python scripts/run_evals.py` chunks, embeds, indexes, retrieves, generates and scores four portfolios over 11 queries with no database, Redis, Docker service or network call, and writes a 4.8 KB `eval_results.json`. Two consecutive runs produce byte-identical files, and a run under Python 3.11.14 (the version `eval.yml` uses) produces a file byte-identical to one under the local Python 3.14. 87 new unit tests pass.

One mid-flight correction is worth recording: the first `MockReviewGenerator` pooled salient terms across all retrieved chunks, and the benchmark run came back with faithfulness of exactly 0.8000 on all four portfolios — a constant, which is precisely the "measures nothing" failure PLAN.md's risk section predicted a mock could introduce. [`6c2d27a`](https://github.com/ChariPramod/pathreview-pramod/commit/6c2d27adf6bb184fb84b5be38838ba9d15312cdc) reworked it to ground each sentence in a single chunk, so a thin chunk produces a claim the faithfulness checker scores as unsupported. The metric now separates the deliberately sparse portfolio (0.60) from the dense ones (0.80).

**Next steps:**
Open the draft PR against the upstream repository with the full template completed, request peer review, and respond to whatever comes back. Then mark the PR ready for review and complete Check-in 2. Four scope questions still need a maintainer's answer and are raised in the PR rather than silently decided: whether actionability is in scope, whether the runner should ever exit non-zero on low scores, whether `eval_results.json` should be committed or ignored, and whether the benchmark and report schemas are acceptable.

**Blockers:**
None blocking implementation. Two pre-existing conditions were measured rather than fixed, so they are not mistaken for regressions later: `make test-unit` fails with 53 pre-existing failures on the base commit (identical failure set before and after this work), and `make lint` reports 182 pre-existing ruff errors, so `make check` exits at its first step and never reaches `black`/`mypy`. Zero of either count comes from files this work adds or edits. Both baselines were captured on the base commit `a730c13` in a separate worktree before any implementation, precisely so the comparison would be defensible.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/658

**Branch:** `feat/40-offline-eval-runner`

**What you built:**
An offline benchmark evaluation runner (`rag/evaluator/benchmark_runner.py`) that drives PathReview's real RAG pipeline — chunking, embedding, indexing, hybrid retrieval, review generation and scoring — over four curated benchmark portfolios and writes a deterministic `eval_results.json`, plus the deterministic `MockReviewGenerator` and `get_review_generator()` factory the pipeline needed to run without a live model. It also repairs `VectorStore.add_chunks`, which raised `AttributeError` on every real `Chunk` and blocked the indexing path entirely. `LLM_PROVIDER=mock python scripts/run_evals.py` now completes with no database, Redis, Docker service or network call.

**Tests added or updated:**
101 new unit tests across five new files; no existing test file needed changing.

- **`tests/unit/test_benchmark_runner.py` (49)** — fixture validation (non-object payload, missing/blank `portfolio_id`, missing `documents`, a document with missing or whitespace-only `text`, duplicate `source_id`, missing `queries`, an empty query string, non-object `profile`, and that every message names the offending file); loading (sorted filename order, missing directory, empty directory, malformed JSON named by file, duplicate `portfolio_id`, and that the four committed fixtures are valid); execution (report schema field-by-field, all scores floats in 0.0–1.0, byte-identical repeated runs, non-zero retrieval proving the BM25 join works, chunk-count floor enforcement, empty-portfolio-list rejection, empty retrieval flagged via `retrieval_empty` rather than an ambiguous 0.0, sections still generated on empty retrieval, no `openai.OpenAI` construction during a full run, temp vector store leaving no residue, unknown provider rejected at construction); aggregation arithmetic (portfolio score equals the mean of its query scores, aggregate equals the mean of portfolio scores, `overall_score` equals `(relevance + faithfulness) / 2`); isolation (a second portfolio's documents never surface in the first's retrieval); grounding inputs (BM25 documents carry the exact ids `VectorStore.add_chunks` derives); empty generated feedback (both no sections and empty-content sections score 0.0 without raising); reproducibility guards (retrieval re-sorted on `(-score, id)`, duplicate chunk text rejected); and report writing (file created, valid JSON, sorted keys, no volatile fields, missing parent directories created, unwritable destination raises `OSError`).
- **`tests/unit/test_run_evals_cli.py` (11)** — exit 0 on success; `eval_results.json` actually created with the expected `portfolio_count`/`llm_provider`; exit 1 plus a stderr message on a missing fixtures directory, on malformed JSON reported by filename, and on an unusable `LLM_PROVIDER`; **no report written when the run fails**; an unwritable output path exits 1 and prints no success line; missing output directories created; repeated CLI runs byte-identical; and `--fixtures-dir`/`--output` defaults matching the paths `eval.yml` expects.
- **`tests/unit/test_mock_generator.py` (20)** — returns a populated `FeedbackSection`; covers all five sections; identical inputs give identical content, confidence and suggestions; output unchanged when chunk order is reversed; content quotes tokens present in the supplied chunks; feedback scores above 0.0 faithfulness against its own context; faithfulness varies with evidence richness and is lower for thin chunks than dense ones; sections cite different chunks and differ from each other; output is not a verbatim copy of any chunk; empty chunks yield an explicit no-evidence section; chunks missing `text` or `score` handled; missing `github_username` handled; unknown section name supported; every sentence clears `FaithfulnessChecker`'s 10-character floor; confidence tracks available evidence; and the module imports no HTTP client.
- **`tests/unit/test_review_generator_provider.py` (12)** — `"mock"` resolves to `MockReviewGenerator`; name normalisation (case/whitespace); unknown and empty names raise `ValueError`; **mock mode constructs no `openai.OpenAI` client**; `openai`/`openrouter` without an API key raise before any client construction; with a key they build a `ReviewGenerator` carrying the right `api_key`, `base_url` and `model`; both implementations satisfy `ReviewGeneratorProtocol`; and the shipped `LLM_PROVIDER` default resolves to an offline generator.
- **`tests/unit/test_vector_store.py` (9)** — `add_chunks` accepts real two-field `Chunk` objects without `AttributeError`; ids follow `BatchEmbeddingProcessor`'s `{source_id}_chunk_{index}` convention; documents and embeddings stay paired; `source_id`/`chunk_index` read from `metadata` rather than attributes; `section` defaults to `""` and is preserved when present; missing metadata keys fall back; empty input performs no upsert; and stored metadata values are all ChromaDB-compatible scalars.

Each of these was mutation-checked rather than assumed: nine deliberate reversions — including restoring the original unconditional success message and reverting `add_chunks` to attribute access — were all detected by the suite (9/9).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

> **Both boxes are deliberately left unchecked, because neither command exits 0 — and neither did before this work.** They are recorded truthfully rather than ticked with a caveat.
>
> | Command | Base commit `a730c13` | This branch | Introduced by this branch |
> |---|---|---|---|
> | `make test-unit` | 53 failed, 375 passed | 53 failed, **476 passed** | **0** — failure sets captured and diffed, identical |
> | `make check` (stops at `ruff`) | 182 errors | 182 errors | **0** — none in any file this branch adds or edits |
> | `mypy` in CI form, Python 3.11 | 99 errors / 25 files | 99 errors / 25 files | **0** — none in the new modules |
>
> `make check` never reaches `black` or `mypy` because `make lint` fails first; that is pre-existing. `black` would also reformat 52 pre-existing files, none of them mine. Every file this branch adds is individually ruff-clean, black-clean and mypy-clean. All 101 new tests pass, on both Python 3.14 (local) and Python 3.11.14 (the version CI uses).

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was received on PR #658 by the end of the module.

**How you responded:**
There was nothing to adopt or reject — [PR #658](https://github.com/ascherj/pathreview/pull/658) is open and ready for review with no submitted reviews, no review comments and no maintainer comments, and issue #40 has no new comments beyond the other students who claimed it. In place of a review cycle I ran a structured self-review against runner determinism, benchmark validation, report schema, temporary vector-store cleanup, mock provider isolation, error handling, CI compatibility, test coverage and documentation accuracy. It surfaced two real defects, both fixed with tests: [`9fd45cb`](https://github.com/ChariPramod/pathreview-pramod/commit/9fd45cb), where retrieval order was not reproducible across processes because `HybridRetriever.retrieve` iterates `set(vector_map) | set(keyword_map)` and Python randomises string hashing per process, fixed in the runner by re-sorting on `(-score, id)` and rejecting portfolios with identical chunk text; and [`17bd4ea`](https://github.com/ChariPramod/pathreview-pramod/commit/17bd4ea), where an unusable `LLM_PROVIDER` surfaced as a raw traceback from inside the provider factory instead of an actionable message and exit 1. After those changes `make test-unit` reports 53 failed / 476 passed with a failure set identical to the captured baseline, `make lint` reports the same 182 pre-existing errors with none in any file this work touches, and the runner's output stays byte-identical across repeated runs, across five `PYTHONHASHSEED` values, and between Python 3.11.14 and Python 3.14. The five open scope questions — actionability, exit-code policy, whether `eval_results.json` is committed or ignored, the benchmark and report schemas, and where `get_review_generator("openai")` should read its model from — are raised in the PR for the maintainer rather than decided silently. Full write-up: [docs/reflections/issue-40-offline-eval-runner.md](docs/reflections/issue-40-offline-eval-runner.md).

---

### Reflection

**What was harder than you expected?**

I read issue #40 as "fill in `scripts/run_evals.py`" and mentally budgeted an evening for it. What I actually ran into was that nothing in the repository had ever composed the RAG stages end to end, so every seam between them was unexercised — and three of them were broken. My first hand-wired probe died immediately on `AttributeError: 'Chunk' object has no attribute 'id'`: `VectorStore.add_chunks` read chunk identity as attributes while the real `Chunk` dataclass is two fields with `source_id`/`chunk_index` tucked inside `metadata`, and the method had zero callers, which is precisely why nobody had noticed. On top of that there was no offline generator at all — `ReviewGenerator` builds its `openai.OpenAI` client in `__init__`, so it raises before you can even call it — and `LLM_PROVIDER=mock`, which both CI workflows set specifically to stay offline, was read by no module in the tree. So the deliverable quietly turned from a script into `rag/evaluator/benchmark_runner.py` plus the missing pieces around it, and the CLI ended up being the smallest part of the work.

**What did you learn about working in a large codebase?**

The instinct to open the file named in the issue and start typing is almost always the wrong first move. Most of what I actually needed lived elsewhere: `.github/workflows/eval.yml` defined the real contract (no `services:` block, `LLM_PROVIDER: mock`, Python 3.11, reads `eval_results.json` from the repo root), `pyproject.toml` excluded `scripts*` from the installed package and therefore decided where the runner could live, and the existing unit tests told me the maintainer's conventions far more reliably than any docstring did. The part that stuck with me is that every module in `rag/` and `ingestion/` was individually competent and they still didn't fit together — `BatchEmbeddingProcessor` indexes chunks correctly but writes to a raw Chroma collection that `HybridRetriever` can't see through `VectorStore`. Contracts only hold where something exercises them, so I got in the habit of tracing the call chain and asking "what actually calls this?" before believing a component worked. It also taught me restraint: `core/services/review_service.py` is visibly stubbed and returns a hardcoded `0.81`, and leaving it untouched was the right call even though fixing it was tempting the whole time.

**How did AI tools help — and where did they fall short?**

I used Claude Code throughout, and it earned its keep on breadth: reading a dozen unfamiliar modules and reporting what calls what, diffing `ReviewGenerator`'s public surface against what the mock had to implement, and generating the bulk of the fixture-validation tests. It made checking the issue's premise cheap — the issue says the eval suite "runs inline during API requests," and a few minutes of grepping showed `EvalSuite` had no runtime callers anywhere, which reframed the entire task before I wrote a line of implementation. Where it fell short was anything that only appears when you actually execute the code. My first `MockReviewGenerator` was plausible and nicely documented and returned faithfulness of exactly 0.8000 on all four portfolios — a constant, which measures nothing — and only running it against the real benchmark set exposed that. The closest call was determinism: three byte-identical runs looked like proof until I went back to `HybridRetriever.retrieve`, noticed the set iteration, and wrote a deliberately adversarial probe across five `PYTHONHASHSEED` values that returned the same chunks in five different orders. Nothing here found itself — the tool sped up the looking, and I still had to run everything, including fixing generated assertions that were simply wrong until I executed them.

**What would you do differently if you started over?**

I'd write the throwaway end-to-end probe on day one, before writing PLAN.md rather than after. That hour of hand-wiring the stages together was the highest-value hour of the whole issue — `AttributeError: 'Chunk' object has no attribute 'id'` reframed the scope in a single stack trace — and doing it first would have made the plan better, not just earlier. I'd also capture the `make test-unit` and `make lint` baseline in Week 7 instead of partway through the build; I got lucky and captured it before touching anything, because otherwise "53 failing tests and 182 ruff errors" would have read as damage I caused rather than a pre-existing condition I could diff against. I'd write the adversarial determinism probe *before* claiming determinism, since "same output twice" and "no source of variance" turned out to be different claims that I conflated for longer than I'd like. And I'd nail down the `eval_results.json` schema up front — I revised its shape more than once late in the work, which churned the aggregation code, and settling that contract early would have saved real time.

**What are you most proud of from this module?**

The easy version of this issue was to make `scripts/run_evals.py` emit a plausible file and call it done, and I could have shipped that in a day. What I'm proud of is that what actually landed is a working offline path — chunking → embedding → indexing → hybrid retrieval → generation → relevance/faithfulness scoring → JSON report — that runs with no database, no Redis, no Docker service and no network, and whose output is byte-identical across repeated runs, across five hash seeds, and between Python 3.11.14 and Python 3.14. Getting there meant finding and repairing integration gaps the issue never mentioned: the broken `Chunk` → `VectorStore` seam, the entirely missing `MockReviewGenerator`, and an `LLM_PROVIDER` switch that both workflows set and no code read. The 101 tests, and the nine deliberate reversions I made to confirm the suite actually fails when the behaviour it guards is broken, are the evidence that I believe the thing works — not the accomplishment itself. And I'm nearly as proud of what I wrote down: the PR states plainly that under mock embeddings this is a regression-and-determinism signal rather than a measurement of review quality, because a number labelled "quality" that is mostly noise is worse than no number at all.
