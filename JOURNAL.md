## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/40

**Issue title:** Implement an offline eval runner that measures review quality across a benchmark portfolio set

**Tier:** [ ] Tier 1  [ ] Tier 2  [x ] Tier 3

**Problem summary:**
The current evaluation suite runs as part of API requests, which makes it difficult
to evaluate the full RAG pipeline independently. This issue adds a standalone
script at `scripts/run_evals.py` that will run the evaluation suite against a
curated collection of benchmark portfolios. The runner should measure review
quality and produce a JSON report containing the resulting scores. The main
areas involved are the new runner script and the existing evaluation logic in
`rag/evaluator/eval_suite.py`.

**Selection notes:**
This issue has a clearly defined output: a command-line evaluation runner that
produces a JSON report. I expect to study the existing evaluation suite, determine
how benchmark portfolios are represented, and reuse the current RAG pipeline
rather than rebuilding evaluation logic. The estimated effort is 7–10 hours, so
I will need to verify that the benchmark data and expected score format are
sufficiently defined before implementation.

**Branch name:** feat/40-offline-eval-runner

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger