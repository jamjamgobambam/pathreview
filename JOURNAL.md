# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method in `rag/evaluator/faithfulness_checker.py`
builds a single context string by joining `chunk.get("text", "")` for every retrieved
chunk. Because `dict.get()` only applies its default when the key is *missing*, a chunk
that explicitly stores `"text": None` returns `None` instead of `""`, and the following
`" ".join(...)` raises a `TypeError`. As a result, any RAG result that contains a chunk
with a null `text` field crashes the faithfulness evaluation instead of returning a score.
A successful fix should coerce `None` (and missing keys) to an empty string before joining,
so malformed chunks are handled gracefully and the related unit test
`test_none_context_chunk_text` passes.

**Branch name:** fix/153-faithfulness-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes / "Is this right for me?" checklist

- **Tier label:** Tier 1 / `good first issue` — explicitly recommended for first-time contributors.
- **Understand the problem:** Yes. The bug is a straightforward `None` handling issue in `str.join()`.
- **Can I reproduce it?** Yes. Running `test_none_context_chunk_text` fails with the exact `TypeError` described in the issue.
- **Scope is limited:** Yes. The fix is localized to one file (`rag/evaluator/faithfulness_checker.py`) and one expression, plus formatting.
- **Existing tests cover it:** Yes. `tests/unit/test_faithfulness_checker.py` already includes `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`.
- **No external API keys needed:** The test runs with `LLM_PROVIDER=mock` and does not require OpenAI or GitHub tokens.
- **Subsystem I can explain:** `rag/evaluator` — the faithfulness scoring step in the RAG pipeline.
- **Realistic to finish in a week:** Yes. The fix and verification took a single session; remaining work is testing, lint, and PR.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/esfahani-moein/codepath_pathreview/commit/3fdf3b9

**Reproduction summary:**
Created `reproduce_issue_153.py` which simulates the original buggy expression
`" ".join([chunk.get("text", "") for chunk in context_chunks])` with input
`[{"text": None}]` and confirms it raises `TypeError: sequence item 0: expected str
instance, NoneType found`. The script then runs the fixed `FaithfulnessChecker.check()`
method on the same input and confirms it returns a valid score (0.0) without crashing.

**PLAN.md link:** https://github.com/esfahani-moein/codepath_pathreview/blob/fix/153-faithfulness-none-text/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
Three pre-existing unit test failures (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`) are unrelated to
this issue — they stem from the stop-word filtering logic in `_is_supported()`. These
should not block the PR for #153 but may need separate issues filed.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix from Week 7 (`chunk.get("text") or ""` in `rag/evaluator/faithfulness_checker.py`,
line 38) is in place and verified. This week I added a new regression test
`test_mixed_none_missing_and_valid_chunks` to `tests/unit/test_faithfulness_checker.py`
covering the PLAN.md mixed-chunk edge case (a `None` chunk, a missing-`text`-key chunk,
and a valid chunk in the same call) — confirming the valid chunk still contributes a
positive score while the malformed chunks no longer crash the join. All three
issue-#153 regression tests pass. Sub-tasks 1–3 from PLAN.md (reproduce, verify with
tests, lint/type-check) are done; sub-task 4 (open PR) is in progress.

**Next steps:**
Run the full `make check` and `make test-unit` to confirm no new failures versus the
documented pre-existing baseline, write the PR description from the repo template, open
a draft PR for peer/mentor feedback, then mark it ready for review and submit the branch
URL.

**Blockers:**
None. The codebase has 52 pre-existing unit-test failures and 181 pre-existing ruff
errors unrelated to this issue; I confirmed my changes add no new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/655

**Branch:** `fix/153-faithfulness-none-text`

**What you built:**
A one-line fix in `FaithfulnessChecker.check()` that coerces `None`/missing `text`
values to `""` before the context-string join (`chunk.get("text") or ""`), so a chunk
with `{"text": None}` no longer raises `TypeError: sequence item 0: expected str
instance, NoneType found` and instead yields a valid faithfulness score (0.0 when no
context is available). Added a regression test for the mixed None/missing/valid chunk
case.

**Tests added or updated:**
- `tests/unit/test_faithfulness_checker.py` — added
  `test_mixed_none_missing_and_valid_chunks` (mixed `None` + missing-key + valid chunk
  call does not crash and the valid chunk still contributes). Existing
  `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` continue to pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*(In a codebase with documented pre-existing failures, "passes" means my changes
introduce no new failures — confirmed above.)*

**Draft PR feedback received from:** none

**Notes on pre-existing failures (for reviewers):**
`make check` and `make test-unit` do not fully pass on `main` independent of this change.
I confirmed my changes introduce **no new** failures:
- `make test-unit`: 52 pre-existing failures across 16 files
  (`test_review_service.py` 13, `test_bias_detector.py` 9, `test_skill_extractor.py` 5,
  `test_resume_parser.py` 5, `test_pii_scrubber.py` 5, `test_faithfulness_checker.py` 3,
  others 12). The 3 `test_faithfulness_checker.py` failures
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) are caused by the stop-word overlap threshold
  in `_is_supported()`, not by this fix. My new test passes.
- `make check` (lint): 181 pre-existing ruff errors across the codebase; the only one in
  the file I touched (`F841` unused `supported` in `test_common_words_filtered_in_overlap`)
  predates this change. `black --check` flags pre-existing multi-line dict formatting in
  the test file (none of my added lines are flagged). `mypy` on
  `rag/evaluator/faithfulness_checker.py` passes clean.
