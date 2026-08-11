# PathReview Development Journal

**Working branch:** https://github.com/christophermayfield/pathreview/tree/feat/40-offline-eval-runner

---

## Week 7

_(Prior portal submit used this same working branch. Week 8/9 work for issue #40 continues below.)_

---

## Week 8 — Reproduction & solution planning

**Issue:** [#40](https://github.com/ascherj/pathreview/issues/40) / B-20 — Implement an offline eval runner that measures review quality across a benchmark portfolio set

**Branch URL (portal submit):** https://github.com/christophermayfield/pathreview/tree/feat/40-offline-eval-runner

**Reproduction commit link:** https://github.com/christophermayfield/pathreview/commit/292b2a368ce6a70f8eaea7a293ca82856629fe31

**Reproduction summary:**
Ran `python3 scripts/run_evals.py`. The script prints success and claims it wrote `eval_results.json`, but the file is never created. Benchmark fixtures under `tests/fixtures/sample_profiles/` are missing, and `EvalResult` has no `actionability_score` despite the stub TODO — locked in with failing tests in `tests/unit/test_run_evals_reproduction.py`.

**PLAN.md link:** https://github.com/christophermayfield/pathreview/blob/feat/40-offline-eval-runner/PLAN.md

**Walkthrough video (recommended):** _(optional — record ≤2 min Loom if desired)_

**Blockers or open questions:**
- No chat/mock LLM exists for `ReviewGenerator` (only mock embeddings). Plan: deterministic mock generator in the runner when `LLM_PROVIDER=mock`.
- `HybridRetriever` never called `keyword_searcher.index(...)` before BM25 search — fix as part of the offline pipeline.

### What I observed

```text
$ python3 scripts/run_evals.py
Running RAG evaluation suite...
Evaluation complete. Results written to eval_results.json

$ ls eval_results.json
# → No such file or directory

$ ls tests/fixtures/sample_profiles/
# → No such file or directory

$ python3 -m pytest tests/unit/test_run_evals_reproduction.py -v
# → 3 failed (missing report file, fixtures, actionability field)
```

### Where the gap lives

| Location | Gap |
|----------|-----|
| `scripts/run_evals.py` | Stub only — TODOs, no real pipeline or file write |
| `rag/evaluator/eval_suite.py` | Relevance + faithfulness only; no actionability |
| `tests/fixtures/sample_profiles/` | Missing entirely |
| `.github/workflows/eval.yml` | Already expects `eval_results.json` after the stub runs |

---

## Week 9 — Implementation

**Issue:** [#40](https://github.com/ascherj/pathreview/issues/40) / B-20 — Offline RAG eval runner

**Branch URL (portal submit):** https://github.com/christophermayfield/pathreview/tree/feat/40-offline-eval-runner

**Implementation commit:** https://github.com/christophermayfield/pathreview/commit/a649251660d840eba8962854540790e8e8809dea

**PLAN.md link:** https://github.com/christophermayfield/pathreview/blob/feat/40-offline-eval-runner/PLAN.md

### What shipped

- `ActionabilityScorer` + `EvalResult.actionability_score` (overall = mean of three metrics)
- Benchmark fixtures: `basic_profile.json`, `strong_profile.json`, `weak_profile.json`
- `HybridRetriever` now indexes BM25 before keyword search
- `scripts/run_evals.py` runs ingest → retrieve → mock/real generate → `EvalSuite` → `eval_results.json`
- Unit tests for actionability + offline runner pass with `LLM_PROVIDER=mock`

### Verify locally

```bash
LLM_PROVIDER=mock python3 scripts/run_evals.py
# Evaluated 3 portfolios | avg overall≈0.453
# (relevance≈0.148, faithfulness≈0.633, actionability≈0.578)

python3 -m pytest tests/unit/test_actionability_scorer.py tests/unit/test_run_evals_reproduction.py -v
# 7 passed
```

### Results

`eval_results.json` includes a `summary` block and per-portfolio scores for relevance, faithfulness, actionability, and overall — matching what CI (`.github/workflows/eval.yml`) comments on PRs.
