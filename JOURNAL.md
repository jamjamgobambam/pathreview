# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker (`rag/evaluator/faithfulness_checker.py`) builds the comparison context by calling `chunk.get("text", "")`, assuming that falls back to an empty string whenever a chunk has no usable text. But `dict.get()` only applies its default when the key is missing entirely — if a chunk instead stores `"text": None` (which happens when upstream parsing produces an empty chunk), `.get()` returns `None`, and the later `" ".join(...)` call crashes with a `TypeError`. In practice this means any RAG evaluation run that touches a document with even one malformed or empty chunk fails outright instead of just treating that chunk as having no content. A successful fix makes the checker handle the `None` case explicitly (e.g. `chunk.get("text") or ""`) so evaluation degrades gracefully rather than crashing, confirmed by the already-stubbed `test_none_context_chunk_text` test in `tests/unit/test_faithfulness_checker.py`.

**Scope check (issue checklist reasoning):** Single file to touch (`rag/evaluator/faithfulness_checker.py`), reproduction steps are already given in the issue, a failing test already exists to validate the fix, no new dependencies or schema changes involved, and the estimated effort (2-3 hours) fits a first issue. This made it a safer pick than the ingestion/pipeline issues, which touch multiple files and have less clear-cut reproduction steps.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`: `rag/evaluator/faithfulness_checker.py` now builds `context_text` with `chunk.get("text") or ""` instead of `chunk.get("text", "")`, so a chunk with `"text": None` degrades to an empty string instead of raising `TypeError`. Added a new test, `test_mixed_none_and_valid_chunk_text`, covering a case not in the original issue: a chunk list with one `None`-text chunk and one valid-text chunk, confirming the valid chunk still contributes to the score. Re-ran `scripts/repro_issue_153.py` from Week 8 and confirmed it now prints a score instead of crashing.

**Next steps:**
Run `make check` and `make test-unit` for real (mid-fix and pre-fix baseline) once local Docker/Postgres setup is fully sorted, commit the fix, and open the PR using the repo template.

**Blockers:**
Local environment setup (Docker Desktop / Postgres connection) was still being finalized as of this check-in — needed before `make test-unit`/`make check` can be run and confirmed.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
