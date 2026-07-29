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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [placeholder until the reproduction commit exists]

**Reproduction summary:**
Running `python3 scripts/run_evals.py` printed a completion message and exited
successfully, but it did not load benchmark cases, invoke the RAG or evaluator
components, or create the reported `eval_results.json` file.

**PLAN.md link:** https://github.com/Ramen-Numeral/pathreview/blob/feat/40-offline-eval-runner/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The repository has no curated benchmark portfolio files or agreed report schema.
The API review path uses a placeholder `_run_rag_retrieval_generation()` helper
and has no `EvalSuite` call site, while the concrete retriever and generator are
not connected through a shared pipeline entry point. The evaluator also exposes
relevance, faithfulness, and overall scores, but no actionability score despite
the runner TODO mentioning one.

### Reproduction evidence

- The documented `make eval` command attempted
  `.venv/bin/python scripts/run_evals.py` and stopped with
  `.venv/bin/python: No such file or directory`.
- To observe the placeholder script itself without creating a virtual
  environment, the reproduction then used `python3 scripts/run_evals.py`;
  `python3` is the Makefile's documented fallback when creating the project
  environment.
- `eval_results.json` was absent before and after the command. The script printed
  `Running RAG evaluation suite...` followed by
  `Evaluation complete. Results written to eval_results.json`.
- `scripts/run_evals.py` currently contains only those messages and TODO comments.
  `tests/benchmarks/` contains only `__init__.py`, and the commented
  `tests/fixtures/sample_profiles/` path does not exist.
- Standalone orchestration belongs in `scripts/run_evals.py`, backed by a shared
  RAG pipeline boundary extracted from the API processing path and scored through
  `rag/evaluator/eval_suite.py`.
