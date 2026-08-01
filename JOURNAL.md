## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker's `check()` method builds its context string from RAG
chunk dictionaries using `chunk.get("text", "")`, assuming this always returns
a string. But `.get()`'s default only applies when a key is missing — if a
chunk's `"text"` key exists but is explicitly set to `None`, `.get()` still
returns `None`, and the following `" ".join(...)` call then crashes with a
`TypeError` since you can't join a `None` value with strings. This lives in
`rag/evaluator/faithfulness_checker.py`, the part of the RAG evaluation
pipeline that checks whether AI-generated review claims are actually
supported by retrieved context. A successful fix would coerce a `None` text
value to an empty string before joining, so faithfulness checking degrades
gracefully instead of crashing whenever ingestion produces a chunk with
missing text content.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vaishnavibollapalli/pathreview/commit/c762598

**Reproduction summary:**
Ran the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py` and confirmed it fails with
`TypeError: sequence item 0: expected str instance, NoneType found` at line
34 of `rag/evaluator/faithfulness_checker.py`, where `chunk.get("text", "")`
returns `None` instead of the default when the chunk's `"text"` key is
explicitly `None`.

**PLAN.md link:** https://github.com/vaishnavibollapalli/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [add Loom link here if you record one]

**Blockers or open questions:**
Still need to grep `ingestion/` and `agent/` to confirm whether the same
`.get("text", ...)` pattern appears elsewhere before finalizing the full fix
scope for Week 9.

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `rag/evaluator/faithfulness_checker.py` — changed
`chunk.get("text", "")` to `chunk.get("text") or ""` (sub-tasks 1–2 from
PLAN.md). Added 2 new unit tests in `tests/unit/test_faithfulness_checker.py`
covering all-None-chunks and mixed-None-and-valid-chunk cases (sub-task 4).
Ran the full `tests/unit` suite and confirmed the fix introduces no new
failures — 377 passed both before and after, with 52 pre-existing failures
unrelated to this change (verified 3 of those in my own test file fail
identically on unmodified `main` via `git stash`). Applied `black`
formatting to both touched files.

**Next steps:**
Open a draft PR, request peer/mentor feedback in Slack, and finalize the PR
description before Sunday's deadline.

**Blockers:**
None.


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/387

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Fixed a `TypeError` crash in `FaithfulnessChecker.check()` that occurred
when a context chunk's `"text"` field was explicitly `None`. Changed
`chunk.get("text", "")` to `chunk.get("text") or ""` so `None` values are
coerced to empty strings before being joined into the context string.

**Tests added or updated:**
Added `test_all_none_context_chunks` and
`test_mixed_none_and_valid_context_chunks` to
`tests/unit/test_faithfulness_checker.py`, covering the case where every
context chunk has `None` text and the case where a `None` chunk is mixed
with a valid one. The existing `test_none_context_chunk_text` (previously
failing) now passes with this fix.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(confirmed via equivalent `ruff`/`black`/`mypy` commands on the two files
this PR touches, since `make` isn't available on Windows PowerShell; 52
pre-existing failures across the full suite are unrelated to this change,
documented in the PR description)

**Draft PR feedback received from:** None