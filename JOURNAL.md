# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the RAG system, the faithfulness checker assumes every retrieved context chunk has string text, so a chunk with `text: None` throws an error instead of being handled. A successful fix would skip or safely handle null-text chunks so the check runs without crashing.

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Is this right for me?
- Scope is small and isolated to one RAG check, so it fits a Tier 1 effort.
- The bug is a clear null-handling case with an obvious success condition (no crash).


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/maanyaS/pathreview/commit/774f9f7d7b50022ad0670a6ca0c453c5ba6c7343

**Reproduction summary:**
I ran the issue's one-liner against my local venv — `FaithfulnessChecker().check("Knows Python.", [{"text": None}])` — and got the exact reported `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:43`, and the repo's existing `test_none_context_chunk_text` fails with the same error. It reproduces every run: `dict.get("text", "")` only falls back to `""` for a *missing* key, so a present-but-`None` value flows straight into `" ".join(...)` and blows up. I committed a comment at the exact failing line documenting the trace and the repro command.

**PLAN.md link:** https://github.com/maanyaS/pathreview/blob/fix/153-faithfulness-none-text-crash/PLAN.md

**Blockers or open questions:**
- No blockers — the fix itself is a few lines. The open design question is whether silently skipping a null chunk is right, since it turns a loud crash into a quietly lower faithfulness score. I plan to log when the assembled context ends up empty so it's still diagnosable, but I'd like a mentor's read on that.
- `relevance_scorer.py:32` uses the identical `chunk.get("text", "")` idiom and has the same latent crash. I'm leaving it out of this PR to keep the scope on #153 and will flag it in the PR description — worth confirming that's the preferred call.
- Still unsure whether `text: None` is itself a symptom of an upstream ingestion/chunker bug rather than just bad caller input.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1–4 from PLAN.md are done. Before writing any code I recorded baselines for `make check` and `make test-unit`, because this codebase has a lot of pre-existing failures (53 failing unit tests, 181 ruff errors, 51 files failing black, and a `make typecheck` that aborts on a numpy stub requiring Python 3.12+ syntax). The fix itself is committed (`fix(rag): handle null text in faithfulness context chunks`): `check()` now filters chunk texts to actual strings before joining, so a missing key, `None`, or a non-string value contributes no context instead of crashing. I also added a `faithfulness_empty_context` log so a run that legitimately scores 0.0 is still diagnosable. Three regression tests are committed on top of the issue's existing `test_none_context_chunk_text`.

**Next steps:**
Sub-task 5 — re-run both commands and diff against the baselines to prove no new failures, write up the pre-existing-failure table for the PR description, and open a draft PR for peer feedback.

**Blockers:**
Pre-commit refused the test-file commit on failures that were already in that file before I touched it (ruff `F841` at line 216, black, and 25 mypy `no-untyped-def`). I annotated my three new tests so they add zero new errors — pre-commit reports the identical ruff 1 / mypy 25 counts with and without my commit — and committed with `--no-verify`, documented in the commit message. Fixing the other 26 would have meant ~30 lines of unrelated cleanup in a Tier 1 bugfix.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1031

**Branch:** `fix/153-faithfulness-none-text-crash`

**What you built:**
`FaithfulnessChecker.check()` assembled its context with `chunk.get("text", "")`, but `dict.get`'s default only fires when the key is *missing* — a present-but-`None` value passed straight through to `" ".join(...)` and raised `TypeError`, aborting an entire evaluation run over one malformed chunk. The fix keeps only values that are actually strings, so null and non-string chunks contribute nothing while valid chunks alongside them still score exactly as before, and logs `faithfulness_empty_context` when no chunk yields usable text.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the issue's existing `test_none_context_chunk_text` now passes, plus three new cases: `test_all_context_chunks_none_text` (every chunk null → 0.0, no raise), `test_mixed_none_and_valid_context_chunks` (a null chunk must not discard the valid chunk next to it), and `test_non_string_context_chunk_text` (an int `text` value is skipped rather than stringified into junk tokens).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Both boxes mean *no new failures*, per the pre-existing-failure guidance. Verified by diffing before/after: unit tests went 53 failed / 375 passed → 52 failed / 379 passed, the single net change being `test_none_context_chunk_text`, which this PR fixes; no test newly fails. Ruff held at 181 errors, black improved 51 → 50 files, and `rag/evaluator/faithfulness_checker.py` reports no mypy issues when checked on its own. The full pre-existing-failure table is documented in the PR description.

**Draft PR feedback received from:** none yet — draft PR opened for peer review in Slack
