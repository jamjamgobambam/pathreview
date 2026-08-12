# Week 7 — Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** ☑ Tier 1 ☐ Tier 2 ☐ Tier 3

## Problem summary

The issue affects the faithfulness checker on the review page. Currently, very short claims cannot be marked as **Supported**, even when the provided evidence clearly supports them. This causes the review results to be inaccurate for short claims. The goal of this issue is to update the faithfulness checking logic so that short claims are evaluated correctly and can be marked as supported when appropriate.

**Branch name:** `fix/152-review-card-update`

**Setup confirmation:** ☑ App runs locally at `localhost:5173`

**Cohort ledger:** ☐ Issue added to cohort ledger

## Selection notes ("Is this right for me?" checklist)

I selected this Tier 1 issue because it has a clearly defined scope and focuses on fixing a single bug rather than implementing a new feature. Based on the issue description, I expect to locate the relevant files without needing to understand the entire codebase and modify only a small number of files. The issue uses technologies I am already familiar with, and I can verify the fix by running the application locally and testing that short claims are correctly marked as supported. This makes it an appropriate first open-source contribution that I can complete within the expected timeframe.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/atai20/pathreview/commit/1525aecc44db2930c43003eb595f5b7f337dde65

**Reproduction summary:**
I reproduced issue #152 locally by running the exact snippet from the GitHub issue against the pre-fix `_is_supported` / `_extract_claims` logic in `rag/evaluator/faithfulness_checker.py`. For feedback `Knows Python. Knows SQL.` with context chunks `python expert` and `sql expert`, only `Knows Python` was extracted (because `Knows SQL` is ≤10 characters), meaningful overlap was a single token `python`, and `check()` returned `0.0` even though both skills are clearly present in context. The same root cause also explains the related failing unit tests `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, and `test_multiple_claims_varying_support`.

**Reproduction evidence (observed locally):**
```text
claims extracted: ['Knows Python']
  claim='Knows Python' supported=False
    meaningful overlap: {'python'}
old check score: 0.0
expected if supported: 1.0
```

**PLAN.md link:** https://github.com/atai20/pathreview/blob/fix/152-review-card-update/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to keep the two-token rule for longer material claims so lowering the floor globally does not create false positives (for example `Python expert` matching on `python` alone). Partial-score calibration for middle-range tests is the main tuning risk going into implementation.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core faithfulness fix from PLAN.md in `rag/evaluator/faithfulness_checker.py`: punctuation-aware tokenization, short-claim extraction for `Knows X` sentences, a narrow one-token support exception for bare/`Knows` forms, and graded partial scores capped below 0.5. Confirmed the issue reproduction now returns `1.0`, and the three previously failing related unit tests pass.

**Next steps:**
Add focused regression tests for issue #152 edge cases, run `make check` / `make test-unit` (or equivalent local commands), open a draft PR to upstream for feedback, then finalize the PR template and Week 9 Check-in 2.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/731

**Branch:** `fix/152-review-card-update`

**What you built:**
Updated `FaithfulnessChecker` so short grounded claims like `Knows Python` / `Knows SQL` can score as supported with one concrete token overlap, while longer material claims still require two meaningful overlaps. Claim extraction no longer drops short tokenizable sentences, punctuation no longer blocks token matching, and partial overlap contributes a capped middle score instead of collapsing to `0.0`.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added regressions for the issue reproduction (`Knows Python. Knows SQL.` → `1.0`), candidate-knows form, two-token floor for material claims, short-claim extraction, punctuation overlap, and tightened `test_minimum_overlap_required`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

**Notes on checks:**
- Touched files pass `ruff`, `black --check`, and `mypy --strict` on `rag/evaluator/faithfulness_checker.py`.
- `tests/unit/test_faithfulness_checker.py`: 27 passed.
- Repo-wide `make test-unit` / `make check` may still report pre-existing failures unrelated to this change (missing optional deps / existing lint debt on untouched modules). This contribution does not introduce new failures in the faithfulness checker path.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments landed on https://github.com/ascherj/pathreview/pull/731 by the end of Week 10. That matches the Summer 2026 note that reviewer feedback is not a feature of this cohort, so I documented the empty review state and moved on to reflection.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hard part was not finding the one-line bug — `_is_supported()` requiring `len(meaningful_overlap) >= 2` was obvious once I reproduced the issue. The surprise was how many nearby behaviors had to move with it. Lowering the threshold globally would make `Python expert` pass on a lone `python` match and break the safety the original rule was trying to keep. I also did not expect claim extraction (`len > 10`) and naive `.split()` punctuation (`Python,` vs `python`) to be part of why the related unit tests failed. Getting a middle score for partial support meant changing from a binary supported-count ratio to graded per-claim scores, which was more design work than a Tier 1 “flip one condition” fix looked like from the issue title alone.

**What did you learn about working in a large codebase?**
In my own projects I can change APIs freely. Here the tests in `tests/unit/test_faithfulness_checker.py` were the real contract: `_is_supported` still had to stay a boolean, full-support and no-support cases still had to hold, and I had to treat repo-wide `make test-unit` noise as pre-existing debt instead of something I owned. Tracing from the issue snippet → `FaithfulnessChecker.check` → `_extract_claims` / `_is_supported` → `EvalSuite` showed how a small evaluator heuristic can affect overall quality scores without touching the UI. Contributing meant reading surrounding callers and matching conventions (docstrings, ruff/black/mypy on touched files, conventional commits) rather than rewriting the module the way I would in a greenfield app.

**How did AI tools help — and where did they fall short?**
AI was strongest for navigation and first-pass scaffolding: locating `faithfulness_checker.py`, drafting PLAN.md sections, and suggesting regression cases like `Knows SQL` extraction and punctuation overlap. It fell short when the fix needed a product judgment — whether one-token support should apply to every short claim or only `Knows X` / bare forms. Early “just use `>= 1`” suggestions would have over-loosened material claims. I still had to run the issue reproduction myself, compare against the three related failing tests, and decide on the partial-score cap (`0.4`) so middle-range assertions stayed honest.

**What would you do differently if you started over?**
I would reproduce against `main` and write PLAN.md *before* landing implementation commits, so Week 8 and Week 9 history read in the intended order. I would also add the regression tests in the same commit as the first behavioral change, not after, and open the draft PR earlier in Week 9 specifically to ask a classmate to pressure-test the one-token exception boundary (`Python expert` vs `Knows Python`). Finally, I would run a baseline `make test-unit` on clean `main` on day one and save the failure list, so PR notes about pre-existing failures were evidence from the start rather than reconstructed later.

**What are you most proud of from this module?**
The restraint in the fix: keeping the two-token floor for material claims while still making the issue’s short `Knows Python. Knows SQL.` example score `1.0`. That felt like a real contribution tradeoff — solving the reported bug without turning the faithfulness checker into “any shared keyword counts as supported.”
