# PLAN.md — B-20 Offline RAG Eval Runner

**Issue:** [#40](https://github.com/ascherj/pathreview/issues/40) / B-20 — Offline RAG eval runner  
**Branch:** `feat/40-offline-eval-runner`  
**Status:** Week 9 implementation complete

## Problem

The course framing says evals run inline during API requests, but in this codebase `EvalSuite` is never called from the API. `scripts/run_evals.py` is a stub: it prints success and claims to write `eval_results.json`, but nothing is written. CI (`.github/workflows/eval.yml`) already expects that file. Benchmark fixtures and an actionability metric (listed in the stub TODO) are also missing.

## Goals

1. Standalone runner that exercises ingest → retrieve → generate → evaluate against curated portfolios
2. JSON quality report for CI PR comments
3. Works with `LLM_PROVIDER=mock` (no API keys in CI)
4. Extend scoring with **actionability** alongside relevance and faithfulness

## Approach

```text
fixtures → chunk + mock embed → ephemeral Chroma → HybridRetriever
        → mock (or real) review generation → EvalSuite → eval_results.json
```

### Step 1 — Actionability scorer

- Add `rag/evaluator/actionability_scorer.py` (heuristic, same style as relevance/faithfulness)
- Extend `EvalResult` with `actionability_score`
- `overall_score = (relevance + faithfulness + actionability) / 3`
- Unit tests under `tests/unit/`

### Step 2 — Benchmark fixtures

Create `tests/fixtures/sample_profiles/`:

| File | Intent |
|------|--------|
| `basic_profile.json` | Mid-level portfolio (G-01 shape: username, resume, two repos) |
| `strong_profile.json` | Richer resume + quantified READMEs |
| `weak_profile.json` | Thin resume + sparse READMEs |

Each includes `eval_query` plus resume/project text for ingestion.

### Step 3 — Fix hybrid keyword indexing

`HybridRetriever.retrieve` loads all chunks but never calls `keyword_searcher.index(...)` before BM25 search, so keyword retrieval is always empty. Fix that one call so offline eval actually exercises hybrid retrieval.

### Step 4 — Implement `scripts/run_evals.py`

- Load `*.json` from fixtures dir
- Per portfolio: temp Chroma dir, mock embeddings, chunk via `StrategySelector`, store via `BatchEmbeddingProcessor` (skip Postgres)
- Retrieve with `HybridRetriever`
- Generate: deterministic mock sections grounded in chunks when `LLM_PROVIDER=mock`; else `ReviewGenerator`
- Score with `EvalSuite`; aggregate into `eval_results.json` (`summary` + per-portfolio scores)

### Step 5 — Verify

- `make eval` / `python scripts/run_evals.py` writes valid JSON
- Reproduction tests flip to passing (or are updated)
- Actionability unit tests pass; no network required in mock mode

## Files to touch

| File | Change |
|------|--------|
| `scripts/run_evals.py` | Real runner |
| `rag/evaluator/eval_suite.py` | Add actionability to result / overall |
| `rag/evaluator/actionability_scorer.py` | New |
| `rag/retriever/hybrid.py` | Index before BM25 search |
| `tests/fixtures/sample_profiles/*.json` | New benchmarks |
| `tests/unit/test_actionability_scorer.py` | New |
| `tests/unit/test_run_evals_reproduction.py` | Update once fixed |

## Risks & unknowns

| Risk | Mitigation |
|------|------------|
| No chat/mock LLM for `ReviewGenerator` (only mock embeddings) | Local mock generator in the runner for `LLM_PROVIDER=mock` |
| `IngestionPipeline` wants a DB session | Bypass DB; use chunk → embed → Chroma collection directly |
| Hybrid BM25 currently dead | Explicit index fix in `hybrid.py` |
| Score heuristics may be noisy | Match existing scorer style; keep CI informational (comment only, no hard gate) |

## Out of scope

- Wiring `EvalSuite` into API `process_review`
- Real OpenAI calls in CI
- Changing `.github/workflows/eval.yml` (already correct once the report exists)

## Success criteria

- [x] `eval_results.json` exists after `python scripts/run_evals.py`
- [x] Report includes relevance, faithfulness, actionability, overall (summary + per portfolio)
- [x] Fixtures load from `tests/fixtures/sample_profiles/`
- [x] Mock mode needs no API keys
