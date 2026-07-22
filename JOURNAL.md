# Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds context by pulling `text` out of each chunk with `chunk.get("text", "")`. That default only applies when the key is missing entirely, whereas if `text` is present but set to `None`, `.get()` returns `None` instead of falling back to an empty string. The code then tries to join all chunk texts together with `" ".join(...)`, which raises a `TypeError` since you can't join a `None` value into a string. This lives in `rag/evaluator/faithfulness_checker.py`. It matters because a chunk with `text: None` is a plausible ingestion artifact, not a rare edge case, so right now it silently crashes faithfulness checking instead of treating the chunk as empty content like the empty string case

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes — "Is this right for me?" checklist**

**Part 1 — Understanding the Issue**
- Can explain it without re-reading: `check()` builds context text from chunks using `chunk.get("text", "")`, but that default only fires when the key is missing, not when it's present with value `None`. So a chunk like `{"text": None}` passes straight through, and the later `" ".join(...)` call crashes with `TypeError`.
- Located the relevant code: `rag/evaluator/faithfulness_checker.py`, in `check()`.
- Done looks like: passing `[{'text': None}]` as a context chunk no longer crashes, it's treated as empty text, same as the missing-key case. `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` should pass.

**Part 2 — Tier Fit**
- Labeled `tier-1` on GitHub. This is my first open-source contribution, so a Tier 1 self-contained fix is the right level: one function, one file, no cross-module reasoning required.

**Part 3 — Codebase Readiness**
- Read `check()` and the surrounding context-building logic in `faithfulness_checker.py`.
- Rough fix plan: replace `chunk.get("text", "")` with `chunk.get("text") or ""` so both a missing key and an explicit `None` value fall back to an empty string.
- Found and read `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` to confirm what the test expects before writing any code.

**Part 4 — Scope and Time**
- Checked the issue comments and ledger: 3 other students are also on #153, plus an open PR (#162) referencing it. Per the checklist, claims are non-exclusive and grading is based on my own artifacts, so I'm fine proceeding — I'll write my own fix and tests independently rather than referencing the existing PR.
- Time estimate: this is a one-line fix plus getting one named test passing — well under the 3–6 hour Tier 1 window, so it's realistic for Weeks 8–9 alongside my other coursework.
- No blockers: issue body names no dependency on other unresolved issues.