# Reproduction — Issue #40: offline eval runner

**Issue:** [Implement an offline eval runner that measures review quality across a benchmark portfolio set](https://github.com/ascherj/pathreview/issues/40)
**Branch:** `feat/40-offline-eval-runner`
**Reproduced on:** 2026-07-26
**Environment:** macOS (Apple Silicon / arm64), project `.venv` on Python 3.14.0, `LLM_PROVIDER=mock`, no Docker services running, no network calls.

This document records what `scripts/run_evals.py` does today, what it is supposed to do, and which
supporting pieces are missing. It is reproduction evidence only — no fix is attempted here.

---

## 1. Commands used

```bash
# Confirm the report does not already exist
ls -la eval_results.json

# Run the eval runner exactly the way CI runs it (.github/workflows/eval.yml)
LLM_PROVIDER=mock .venv/bin/python scripts/run_evals.py; echo "EXIT_CODE=$?"

# Confirm whether the run produced the report
ls -la eval_results.json
git status --porcelain

# Confirm the benchmark fixtures referenced by the runner's TODO
ls -la tests/fixtures/sample_profiles/
ls -la tests/benchmarks/

# Confirm which symbols exist / are called
grep -rn "EvalSuite" --include="*.py" .
grep -rni "actionab" --include="*.py" .
grep -rn "llm_provider\|get_embedding_provider" --include="*.py" .
grep -rn "get_llm_provider\|MockGenerator\|MockLLM" --include="*.py" .
```

Two throwaway probe scripts (kept out of the repository, run from a scratch directory) wired the real
`ingestion/` and `rag/` components together offline to establish how far the "full RAG pipeline" can
actually be assembled today. Their findings are in §4.

---

## 2. Observed behaviour

### 2.1 The runner is a stub that reports success without doing anything

```
$ LLM_PROVIDER=mock .venv/bin/python scripts/run_evals.py; echo "EXIT_CODE=$?"
Running RAG evaluation suite...
Evaluation complete. Results written to eval_results.json
EXIT_CODE=0
```

```
$ ls -la eval_results.json
ls: eval_results.json: No such file or directory

$ git status --porcelain
(no output — the run creates and modifies nothing)
```

The process exits **0** and prints `Results written to eval_results.json`, but **no file is written**.
The success message is unconditional text in [scripts/run_evals.py:12](scripts/run_evals.py#L12); the
body of `main()` is a four-line TODO comment
([scripts/run_evals.py:7-11](scripts/run_evals.py#L7-L11)). Nothing is loaded, executed, or scored.

This is worse than a plain no-op: the exit code and the message both signal success, so neither a
developer nor CI can distinguish "evaluation passed" from "evaluation never ran".

### 2.2 CI silently degrades as a result

[.github/workflows/eval.yml](.github/workflows/eval.yml) runs `python scripts/run_evals.py` with
`LLM_PROVIDER: mock`, then reads `eval_results.json` and posts it as a PR comment. Because the step
exits 0 and no file appears, the `readFileSync` in the `try` block throws, is swallowed by the empty
`catch (e) {}`, and the job posts:

````text
## RAG Evaluation Results
```json
Eval results not found.
```
````

The workflow itself never fails. Every PR touching `rag/**`, `ingestion/chunking/**`, or
`ingestion/embeddings/**` gets a green check and a "not found" comment.

### 2.3 Benchmark fixtures do not exist

```
$ ls -la tests/fixtures/sample_profiles/
ls: tests/fixtures: No such file or directory

$ ls -la tests/benchmarks/
-rw-r--r--  __init__.py    (0 bytes — the only file)
```

`tests/fixtures/` does not exist at all, even though
[scripts/run_evals.py:8](scripts/run_evals.py#L8) names `tests/fixtures/sample_profiles/` as the
benchmark source. There is no benchmark portfolio, no benchmark schema, no golden output, and no
score threshold anywhere in the repository.

### 2.4 There is no mock generation provider

`grep -rn "get_llm_provider\|MockGenerator\|MockLLM" --include="*.py" .` returns **no matches**.

The only provider factory in the codebase is
[`get_embedding_provider`](ingestion/embeddings/provider.py#L103), which covers **embeddings**
(`"mock"` / `"openai"`) — not generation. Generation has exactly one implementation,
[`ReviewGenerator`](rag/generator/review_generator.py#L24), which builds a live `openai.OpenAI`
client in its constructor ([rag/generator/review_generator.py:34-37](rag/generator/review_generator.py#L34-L37)).

Constructing it offline fails **before** any generation call is made:

```
ReviewConfig(api_key="", base_url="https://openrouter.ai/api/v1", model="x")
ReviewGenerator(cfg)
-> OpenAIError: Missing credentials. Please pass an `api_key`, ... or set the OPENAI_API_KEY ...
```

So the generation stage of the "full RAG pipeline" cannot be exercised offline at all today.

### 2.5 `LLM_PROVIDER=mock` is not wired to anything

`Settings.llm_provider` is declared at [core/config.py:16](core/config.py#L16) with default `"mock"`,
and `LLM_PROVIDER: mock` is set in [.github/workflows/eval.yml](.github/workflows/eval.yml#L23) and
twice in [.github/workflows/ci.yml](.github/workflows/ci.yml#L46). A grep across the codebase shows
**no module reads `settings.llm_provider`**, and **`get_embedding_provider()` has no callers** — it
is only defined and exercised by `tests/unit/test_llm_provider_contract.py`.

The env var that CI sets to force offline behaviour is therefore currently inert.

### 2.6 Actionability is named but not implemented

[scripts/run_evals.py:10](scripts/run_evals.py#L10) says to "Score retrieval relevance, faithfulness,
and actionability". A case-insensitive search for `actionab` across all `*.py` files matches **only
that comment**. [`EvalSuite`](rag/evaluator/eval_suite.py#L20) implements relevance and faithfulness
only, and computes `overall = (relevance + faithfulness) / 2`
([rag/evaluator/eval_suite.py:46](rag/evaluator/eval_suite.py#L46)). No actionability scorer exists
in `rag/` or anywhere else.

### 2.7 `EvalSuite` has no runtime callers

`grep -rn "EvalSuite" --include="*.py" .` matches only its own definition in
[rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py). The issue states that "the current eval
suite runs inline during API requests" — in the code as it stands it does **not** run anywhere.
[`process_review()`](core/services/review_service.py#L82) delegates to `_run_ingestion_pipeline`,
`_run_agent_orchestration`, `_run_rag_retrieval_generation`, and `_run_safety_checks`, all of which
return hardcoded placeholder dictionaries (e.g. the fixed `"overall_score": 0.81` in
[core/services/review_service.py](core/services/review_service.py)). The request path never calls
`HybridRetriever`, `ReviewGenerator`, or `EvalSuite`.

---

## 3. Expected behaviour

Per the issue and the CI contract, `python scripts/run_evals.py` with `LLM_PROVIDER=mock` should:

1. Load a curated set of benchmark portfolios from a fixture location in the repository.
2. Run each portfolio through the retrieval + generation + scoring path using deterministic,
   non-networked components.
3. Produce quality scores per portfolio plus an aggregate.
4. Write a machine-readable `eval_results.json` to the repository root.
5. Complete with no external services (no Postgres, Redis, or Chroma container) and no API calls,
   on Python 3.11, so the `eval.yml` job can read and publish the report.
6. Be reproducible: the same inputs must yield byte-identical scores across runs.

None of steps 1–5 happens today; only the exit code is (misleadingly) correct.

---

## 4. What actually works offline today (probe findings)

Wiring the real components together by hand confirmed which parts of the pipeline are usable and
where it breaks. This matters because it determines how much of #40 is "write a runner" versus
"make the pipeline runnable at all".

| Stage | Component | Offline result |
|---|---|---|
| Chunking | `StrategySelector.chunk(text, metadata)` | **Works.** Produces `Chunk(text, metadata)` with `source_id`, `chunk_index`, `char_start`, `char_end` in `metadata`. |
| Embedding | `MockEmbeddingProvider.embed` | **Works, deterministic.** 1536-dim, identical vectors across runs. |
| Vector store | `VectorStore(persist_dir=...)` | **Constructs.** Embedded `chromadb.PersistentClient` — no container needed. |
| Vector indexing | `VectorStore.add_chunks` | **Fails — see §4.1.** |
| Keyword search | `KeywordSearcher.index` / `.search` | **Works.** BM25 over in-memory chunks. |
| Hybrid retrieval | `HybridRetriever.retrieve` | **Works** once the collection is populated and the keyword index is built — but degrades silently otherwise (§4.2). |
| Generation | `ReviewGenerator` | **Fails at construction** without an API key (§2.4). |
| Scoring | `EvalSuite.run` | **Works, deterministic.** Returned `EvalResult(relevance_score=0.75, faithfulness_score=1.0, overall_score=0.875)` on a sample. |

### 4.1 `VectorStore.add_chunks` is incompatible with the `Chunk` objects the chunkers produce

```
vs.add_chunks(list(zip(chunks, embeddings)), "profile_bench01")
-> AttributeError: 'Chunk' object has no attribute 'id'
   at rag/retriever/vector_store.py:56  ->  ids.append(chunk.id)
```

[`Chunk`](ingestion/chunking/base.py) is a dataclass with exactly two fields, `text` and `metadata`.
[`VectorStore.add_chunks`](rag/retriever/vector_store.py#L46) reads `chunk.id`, `chunk.source_id`,
`chunk.chunk_index`, and `chunk.section` as **attributes**, none of which exist — the chunkers place
`source_id` and `chunk_index` inside `metadata` instead. Confirmed directly:

```
Chunk dataclass fields: dict_keys(['text', 'metadata'])
chunk.metadata keys:    ['char_end', 'char_start', 'chunk_index', 'source_id', 'source_type']
hasattr(chunk, 'id')           -> False
hasattr(chunk, 'source_id')    -> False
hasattr(chunk, 'chunk_index')  -> False
hasattr(chunk, 'section')      -> False
```

Separately, [`BatchEmbeddingProcessor._store_embedding`](ingestion/embeddings/batch_processor.py)
writes through a *different* path — it calls `self.vector_db.add(...)` on a raw Chroma collection and
derives the id from `chunk.metadata["source_id"]` / `chunk.metadata["chunk_index"]`, i.e. correctly.
So there are two mutually incompatible indexing paths, and the one `HybridRetriever` reads from
(`VectorStore`) is the broken one. Populating the collection required bypassing `add_chunks` and
calling `collection.upsert(...)` directly.

Note also that `IngestionPipeline` is not usable in an offline runner regardless: its `_check_skip`
calls `self.db_session.query(...)`, so it requires a database session.

### 4.2 `HybridRetriever` degrades silently when the keyword index is not built

`HybridRetriever.retrieve` computes `all_chunks = self._get_all_chunks(collection_name)` and then
**never uses it** — the caller is responsible for having called `KeywordSearcher.index(...)` first.
If they have not, the BM25 half contributes 0.0 to every blended score and the call still succeeds:

```
CASE A (keyword searcher NOT indexed):  4 results, every keyword_score = 0.0
CASE B (indexed, chunks carry "id"):    4 results, top result keyword_score = 1.0
```

The same silent degradation happens when the indexed chunk dicts lack an `"id"` key: `retrieve` builds
`keyword_map = {r.get("id", ""): r ...}`, so every keyword hit collapses onto the `""` key and is
discarded. Confirmed — CASE D returned results identical to the un-indexed CASE A.

### 4.3 Mock embeddings carry no semantic signal

`MockEmbeddingProvider` seeds a RNG from a SHA-256 of the text, so vectors for related texts are
essentially orthogonal. Cosine similarity against the query `"Python FastAPI REST APIs"`:

| Candidate text | cosine |
|---|---|
| `Built REST APIs using Python and FastAPI` (paraphrase) | **+0.054** |
| `Python FastAPI REST API backend development` (paraphrase) | **+0.022** |
| `React TypeScript Tailwind weather forecasting app` (unrelated) | **+0.000** |

Under `LLM_PROVIDER=mock`, vector ranking is therefore effectively random, and BM25 is the only stage
carrying real retrieval signal. This does not block the runner, but it constrains what its scores can
honestly claim to measure — see the plan's "Risks & unknowns".

### 4.4 BM25 scores can be negative on a small corpus

With a single-document corpus the probe observed `bm25_score = -0.824`. `HybridRetriever` normalises
via `keyword_score / keyword_scores_max`; a negative maximum inverts the ranking, and the
`min_score` filter (default `0.3`, [core/config.py](core/config.py)) can then discard everything.
With a 4-chunk corpus the scores were `[1.670, 0.0, 0.0, 0.0]` and behaved normally. Benchmark corpus
size is therefore load-bearing for score stability.

---

## 5. Relevant files

**Feature gap lives here**

| File | Role |
|---|---|
| [scripts/run_evals.py](scripts/run_evals.py) | The stub runner. `main()` prints and returns; the whole feature is missing. |
| [.github/workflows/eval.yml](.github/workflows/eval.yml) | Consumer of `eval_results.json`; defines the offline/CI contract. |
| `tests/fixtures/sample_profiles/` | Referenced by the runner's TODO — **does not exist**. |

**Components the runner must drive**

| File | Role |
|---|---|
| [rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py) | `EvalSuite.run(query, chunks, feedback)` → `EvalResult`. Works offline; no callers. |
| [rag/evaluator/relevance_scorer.py](rag/evaluator/relevance_scorer.py) | Deterministic keyword-overlap relevance. |
| [rag/evaluator/faithfulness_checker.py](rag/evaluator/faithfulness_checker.py) | Deterministic claim-support faithfulness. |
| [rag/retriever/hybrid.py](rag/retriever/hybrid.py) | Blends vector + BM25; silent-degradation behaviour in §4.2. |
| [rag/retriever/vector_store.py](rag/retriever/vector_store.py) | Embedded Chroma; `add_chunks` broken per §4.1. |
| [rag/retriever/keyword_search.py](rag/retriever/keyword_search.py) | BM25 index/search. |
| [rag/generator/review_generator.py](rag/generator/review_generator.py) | Only generation path; requires a live OpenAI client. |
| [rag/generator/output_parser.py](rag/generator/output_parser.py) | `FeedbackSection` + `parse_review_output`. |
| [ingestion/embeddings/provider.py](ingestion/embeddings/provider.py) | `MockEmbeddingProvider`, `get_embedding_provider` (uncalled). |
| [ingestion/chunking/strategy_selector.py](ingestion/chunking/strategy_selector.py) | Produces `Chunk` objects offline. |
| [ingestion/chunking/base.py](ingestion/chunking/base.py) | `Chunk(text, metadata)` — the shape `add_chunks` disagrees with. |
| [core/config.py](core/config.py) | `llm_provider`, `max_chunks_per_query`, `min_relevance_score`. |

**Context only — must not change for this issue**

| File | Why it is context |
|---|---|
| [core/services/review_service.py](core/services/review_service.py) | Shows the stubbed request path and that `EvalSuite` is uncalled. Out of scope. |
| [api/routes/reviews.py](api/routes/reviews.py) | Request entry point; API behaviour must not change. |
| [ingestion/pipeline.py](ingestion/pipeline.py) | DB-coupled ingestion; unusable offline, not to be refactored here. |
| [docker-compose.yml](docker-compose.yml) | The runner must not depend on it. |

---

## 6. Confirmed feature gap

1. **`scripts/run_evals.py` implements none of the feature.** It prints a hardcoded success message,
   writes no file, and exits 0 — verified by running it and by an empty `git status`.
2. **`eval_results.json` is never produced.** Verified absent before and after the run.
3. **Benchmark portfolio fixtures do not exist.** `tests/fixtures/` is absent entirely;
   `tests/benchmarks/` holds only an empty `__init__.py`.
4. **No mock generation provider exists.** No `get_llm_provider`, `MockGenerator`, or `MockLLM`
   anywhere; `ReviewGenerator` raises `OpenAIError` at construction without credentials. The mock
   factory that does exist covers embeddings only.
5. **Actionability scoring does not exist.** Named once in a comment; implemented nowhere.
6. **Full pipeline orchestration does not exist**, and cannot simply be lifted from the request path:
   `process_review()`'s stages return hardcoded stubs and never invoke the real RAG components.
7. **The pipeline is not currently assemblable end-to-end without a fix:**
   `VectorStore.add_chunks` raises `AttributeError` on the `Chunk` objects the chunkers emit (§4.1).
8. **`LLM_PROVIDER=mock` is inert** — nothing in the codebase reads `settings.llm_provider`, so the
   switch CI relies on to stay offline currently has no effect (§2.5).

Items 7 and 8 were not visible from the issue text and are the reason this is an integration task
rather than a scripting task.
