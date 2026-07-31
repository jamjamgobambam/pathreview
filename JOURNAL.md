# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method builds its context string by pulling
`text` out of each chunk dict with `chunk.get("text", "")`, assuming that
missing keys are the only case it needs to guard against. But `.get()` only
falls back to the default when the key is absent — if a chunk explicitly has
`"text": None`, `.get()` returns `None`, and the subsequent `" ".join(...)`
call raises a `TypeError` because it can't join a `NoneType` into a string.
In practice this means any upstream chunk that legitimately has a null/empty
text field (rather than a missing one) crashes the faithfulness check instead
of being skipped or treated as empty. A correct fix should coerce `None`
values to an empty string (or filter the chunk out) before joining, so the
checker degrades gracefully instead of raising. This touches
`rag/evaluator/faithfulness_checker.py`, and there's already a failing test,
`test_none_context_chunk_text`, in `tests/unit/test_faithfulness_checker.py`
that should pass once the fix is in.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/adedotdev/pathreview/commit/966b683 (branch `fix/153-faithfulness-checker-none-text`)

**Reproduction summary:**
Ran the existing (failing) test `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`, which calls `FaithfulnessChecker.check()` with a chunk `{"text": None}`. It raised `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:39`, confirming `chunk.get("text", "")` returns `None` (not the default) when the key is present but explicitly `None`. Documented the reproduction with an inline comment at the crash site.

**PLAN.md link:** https://github.com/adedotdev/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** _not recorded yet_

**Blockers or open questions:**
The same `chunk.get("text", "")` pattern also exists in `review_generator.py`, `relevance_scorer.py`, and `hybrid.py` and likely has the same latent bug, but issue #153 only scopes the fix to `faithfulness_checker.py`. Also, 3 tests in `test_faithfulness_checker.py` fail today for reasons unrelated to this issue (claim-extraction/overlap-scoring logic) — need to confirm with a mentor whether that's separately tracked before I touch it in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: `faithfulness_checker.py` now builds
`context_text` with `chunk.get("text") or ""` instead of
`chunk.get("text", "")`, so a chunk with `"text": None` is treated the same as
a missing/empty one instead of crashing. `test_none_context_chunk_text` now
passes. Added `test_mixed_none_missing_and_valid_text_chunks` to cover a
`context_chunks` list with `None` text, a missing key, and valid text in the
same call (PLAN.md's "mixed" edge case) — it passes too.

Before changing anything I captured a baseline: `pytest tests/unit -m unit`
had 53 pre-existing failures unrelated to #153 (bias detector, PII scrubber,
resume parser, review service, etc. — none touch faithfulness/context
handling). After the fix, the suite has 52 failures — the exact same set
minus `test_none_context_chunk_text`, confirmed via diff. `ruff check` and
`black --check` on the two touched files show only pre-existing issues I
didn't introduce (an unsorted-import warning already in
`faithfulness_checker.py`, and an unused-variable warning in an untouched
test method) — my own added/changed lines are clean. `mypy` on
`faithfulness_checker.py` alone passes; a full-tree `mypy` run fails in this
environment due to missing third-party type stubs (`PyPDF2`, `jose`,
`passlib`, `rank_bm25`) and a numpy stub/Python-version mismatch, all
pre-existing and unrelated to this change.

**Next steps:**
Open a draft PR referencing #153, share it in Slack for early feedback, then
finalize once reviewed.

**Blockers:**
No `make` binary available in this Windows/Git Bash environment, so I ran the
underlying `pytest`/`ruff`/`black`/`mypy` commands directly from a local
`.venv` instead of `make check`/`make test-unit` — same commands the
Makefile wraps, just invoked without `make`.
