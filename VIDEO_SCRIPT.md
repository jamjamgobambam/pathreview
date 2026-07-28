# Walkthrough video script — Issue #153 (≤ 2 minutes)

**Target length:** ~110 seconds. Screen: terminal + editor, no slides needed.

---

**[0:00–0:15] Intro (15s)**
> "This is issue #153 on PathReview: the faithfulness checker crashes when a retrieved context chunk has `text: None`. I'll reproduce the crash, then walk through my fix plan."

**[0:15–0:45] Reproduce the bug (30s)**
- Show `rag/evaluator/faithfulness_checker.py` lines 33-36 on screen, point at:
  `chunk.get("text", "") for chunk in context_chunks`
> "The bug is here — `.get()`'s default only kicks in when the key is *missing*. If the key exists but its value is `None`, `.get()` still returns `None`."
- Run in terminal:
  ```
  python -c "from rag.evaluator.faithfulness_checker import FaithfulnessChecker; FaithfulnessChecker().check('Knows Python.', [{'text': None}])"
  ```
- Point at the traceback: `TypeError: sequence item 0: expected str instance, NoneType found`.
> "Same crash the issue describes."
- Run `pytest tests/unit/test_faithfulness_checker.py -v` and show `test_none_context_chunk_text` failing — the regression test that already encodes this bug.

**[0:45–1:30] Walk through the plan (45s)**
- Open `PLAN.md`.
> "The fix is a one-line change in `check()`: swap `chunk.get("text", "")` for `chunk.get("text") or ""`, so a `None` value collapses to an empty string exactly like a missing key already does."
- Scroll to the files table.
> "Only `faithfulness_checker.py` changes — the existing tests, `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`, already cover both cases, so no new test files are required."
- Scroll to the edge cases section.
> "A few things I flagged: mixed chunk lists shouldn't lose valid chunks when one is `None`; the same `.get('text', '')` pattern shows up in `relevance_scorer.py`, `review_generator.py`, and `hybrid.py` — same footgun, but out of scope for this issue, so I'm leaving those alone and calling them out for a follow-up. I also confirmed there are three pre-existing, unrelated failing tests in this file from scoring-threshold logic — not something this PR should touch."

**[1:30–1:55] Wrap-up (25s)**
> "Next step is implementing the one-line fix, confirming the full suite and `make check` pass, then opening the PR referencing `Fixes #153`. That's the plan — thanks for watching."

**[1:55–2:00] End.**

---

### Recording checklist
- [ ] Terminal font size large enough to read on screen recording
- [ ] Pre-open `faithfulness_checker.py`, `PLAN.md`, and a terminal tab in the repo root
- [ ] Have the repro command and `pytest -v` command ready in shell history
- [ ] Keep total runtime under 2:00
