## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None
**Link:** https://github.com/ascherj/pathreview/issues/153

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- When retrieving context chunks for the RAG pipeline, a chunk's `text` field can sometimes be `None` instead of an empty string or missing entirely. The `FaithfulnessChecker.check()` method uses `chunk.get("text", "")` to build context text, but `.get()`'s default only applies when the key is missing — not when the value is `None`. This causes `" ".join(...)` to raise a `TypeError` since it can't join a `NoneType`.
- Expected: the function should return a faithfulness score (0.0–1.0) even when `text` is `None`. Actual: it raises a `TypeError` instead.

### Map
Which files, functions, or modules are involved?
- I expect to only modify `rag/evaluator/faithfulness_checker.py`. The existing test `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text` already covers this case and should pass once the fix is applied — no new test file should be needed.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Modify `rag/evaluator/faithfulness_checker.py` (lines 34–36) — change `chunk.get("text", "")` to `chunk.get("text") or ""` so a `None` value falls back to an empty string, same as a missing key.
2. Run `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` to confirm it now passes instead of raising `TypeError`.
3. Run the full test file (`pytest tests/unit/test_faithfulness_checker.py -v`) to make sure the fix doesn't break other passing tests (e.g. `test_missing_text_key_in_chunk`).
4. Manually re-run the earlier reproduction (`FaithfulnessChecker().check('Knows Python.', [{'text': None}])`) to confirm it now returns a float score instead of crashing.
5. Commit the fix with a Conventional Commit message (e.g. `fix(rag): handle None text value in context chunks`) referencing issue #153.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- **Input:** `context_chunks` — a list of dicts passed to `FaithfulnessChecker.check()`, where each dict may or may not have a `"text"` key, and that key's value can be a string, `None`, or missing entirely.
- **Output (before fix):** raises `TypeError` when any chunk's `text` is `None`.
- **Output (after fix):** returns a float faithfulness score between 0.0 and 1.0, treating a `None` text value the same as an empty string — no crash, same behavior as the existing "missing key" case.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- The `or ""` fallback treats any falsy `text` value (e.g. `""`, `0`, `False`) the same as `None`, not just `None` specifically — this should be fine here since `text` is expected to always be a string or `None`, but it's a subtly different guarantee than an explicit `is None` check.
- I haven't checked whether other parts of the RAG pipeline (e.g. the retriever or ingestion code) can also produce chunks with `None` text — if so, this fix only patches the symptom in `FaithfulnessChecker`, not the upstream cause of why `text` is ever `None` in the first place.
- I'm not fully certain this is the only place in the codebase with the same `.get(key, default)` pitfall — similar bugs could exist elsewhere if other files use the same chunk structure.

**Pre-existing baseline (before my fix):**
- `make check` (lint/format/typecheck): fails with 182 pre-existing ruff errors across many unrelated files (e.g. `safety/content_filter.py`, `tests/unit/test_tech_detector.py`) — none in `rag/evaluator/faithfulness_checker.py`.
- `make test-unit`: 53 failed, 375 passed (pre-existing, unrelated to issue #153).
- After applying my fix, I will re-run both commands and confirm the failure counts don't increase, and that `test_none_context_chunk_text` specifically now passes.

### Edge cases
What inputs or states should your fix handle gracefully?
- A chunk with `"text": None` (the reported bug) — should be treated as empty text, not crash.
- A chunk missing the `"text"` key entirely — already handled correctly before the fix; must keep working the same way.
- A chunk with `"text": ""` (explicit empty string) — should behave the same as `None` or missing.
- Multiple chunks in `context_chunks`, where some have valid text and others have `None` — only the `None` ones should be treated as empty; valid text should still be included in `context_text`.
- An entire `context_chunks` list where every chunk has `None` text — should still return a score (likely 0.0, since there's no supporting context) rather than crash.