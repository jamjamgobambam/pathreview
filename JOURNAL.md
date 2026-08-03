# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`FaithfulnessChecker.check()` builds the context string by calling
`chunk.get("text", "")` on each retrieved chunk. That default only applies when
the `"text"` key is missing entirely — if the key exists but is explicitly set
to `None`, `.get()` returns `None` instead of falling back to `""`. The
resulting list of chunk texts then gets passed to `" ".join(...)`, which
raises a `TypeError` because `join` requires every item to be a string. A
successful fix will coerce a `None` (or otherwise falsy/non-string) `"text"`
value to an empty string before joining, so a single malformed chunk no
longer crashes the whole evaluation run. This affects
`rag/evaluator/faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-context-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ateressa/pathreview/commit/f7d5571

**Reproduction summary:**
Ran `pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text`,
an existing test that calls `check()` with `context_chunks = [{"text": None}]`.
It fails with `TypeError: sequence item 0: expected str instance, NoneType found`,
raised from the `" ".join(...)` call in `FaithfulnessChecker.check()` — confirming
`chunk.get("text", "")` doesn't catch an explicit `None` value, only a missing key.

**PLAN.md link:** https://github.com/ateressa/pathreview/blob/fix/153-faithfulness-checker-none-context-text/PLAN.md

**Blockers or open questions:**
`relevance_scorer.py:32` has the same `chunk.get("text", "")` pattern and may have
an identical latent crash reachable through `EvalSuite.run()`. Leaving it out of
this issue's scope but may file a follow-up.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 1: `rag/evaluator/faithfulness_checker.py`
now builds `context_text` with `chunk.get("text") or ""` instead of
`chunk.get("text", "")`, so a chunk with an explicit `"text": None` falls back to
`""` the same way a missing key already did. `test_none_context_chunk_text` now
passes, and `test_missing_text_key_in_chunk` (the already-passing case) is
unaffected. Manually exercised `FaithfulnessChecker.check()` with a
`[valid_chunk, {"text": None}]` list — returns a normal float (`1.0`) instead of
crashing.

Also confirmed the PLAN.md risk: `EvalSuite.run()` still crashes on the same
input, but via `RelevanceScorer.score()` → `_tokenize()` calling `.lower()` on
`None` (`relevance_scorer.py:32-33`) — a separate, identical bug in a different
file. Staying out of scope for #153 per the plan; noting it as a likely
follow-up issue.

Ran `make test-unit` and `make check` before and after the fix (stashing/popping
the change to diff) to separate pre-existing failures from anything new:
- `make test-unit`: 53 failed / 375 passed before, 52 failed / 376 passed after
  — exactly the one target test flipping to passing, no other change.
- `make check`: 181 pre-existing `ruff` errors, identical count with and without
  the fix (none in `faithfulness_checker.py`); `black` and `mypy` run clean on
  the touched file. Pre-existing `black` drift and a `mypy` gap in
  `eval_suite.py:23` (untouched file) are unrelated to this change.

**Next steps:**
Update PR description to document the pre-existing failures and the
`relevance_scorer.py` follow-up, then open the draft PR for peer/mentor review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/528

**Branch:** `fix/153-faithfulness-checker-none-context-text`

**What you built:**
`FaithfulnessChecker.check()` was crashing with `TypeError` whenever a
retrieved context chunk had `"text": None` instead of a real string or a
missing key, because `chunk.get("text", "")` only falls back to `""` for an
absent key, not an explicit `None`. Changed the lookup to
`chunk.get("text") or ""` so a `None` value is coerced to empty the same way a
missing key already was, and a single malformed chunk no longer takes down the
whole evaluation run.

**Tests added or updated:**
No new test file — `tests/unit/test_faithfulness_checker.py` already had
`test_none_context_chunk_text` (previously failing, now passing) and
`test_missing_text_key_in_chunk` (already passing, confirmed unaffected)
encoding the expected behavior.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(both pass in the sense required for this codebase: 52 pre-existing failures
in `make test-unit` and 181 pre-existing `ruff` errors in `make check` are
unchanged with the fix in vs. out — documented in the PR description — and
this change introduces no new failures.)*

**Draft PR feedback received from:** none — posted in Slack for mentor/peer
review and waited a couple of days with no response. Marking ready for review
and submitting to meet the hard deadline.
