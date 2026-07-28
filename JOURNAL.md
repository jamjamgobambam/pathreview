# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation layer builds a single context
string by joining the `text` field of every retrieved context chunk. It reaches
for each chunk's text with `chunk.get("text", "")`, assuming a missing value
falls back to an empty string. That assumption breaks when a chunk actually
contains the key `text` set to `None`: `.get()` only substitutes the default
when the key is absent, so it returns `None`, and the following `" ".join(...)`
raises `TypeError: sequence item 0: expected str instance, NoneType found`. As a
result, a single null-text chunk crashes the whole faithfulness check instead of
being treated as empty context. A successful fix makes `check()` coerce
`None` (and any non-string) chunk text to `""` so the join is robust, letting
the score be computed from the remaining valid chunks. This lives in
`rag/evaluator/faithfulness_checker.py` (the `check()` method, ~lines 34–35),
covered by the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope reasoning

- **Do I understand the bug?** Yes. It is a Python `dict.get()` semantics
  gotcha (default is only used for *absent* keys, not `None` values) that
  surfaces as a `TypeError` in a `str.join`. Confirmed the exact line locally at
  `rag/evaluator/faithfulness_checker.py:34-35`.
- **Is the scope contained?** Yes — one method in one file. It does not touch
  the API, database, migrations, or frontend, so there is little risk of scope
  creep.
- **Do I have the skills?** Yes — standard Python; no new framework or domain
  knowledge required.
- **Is it reproducible / testable?** Yes. The issue includes a two-line repro,
  and a failing unit test (`test_none_context_chunk_text`) already exists, so I
  can verify the fix objectively with `make test-unit`.
- **Tier fit:** Labeled `tier-1` and `good first issue` — appropriate for a
  first contribution to a large codebase.
- **Watch-out:** The issue references a related PR (#211). Before opening my own
  PR I will check whether that PR already resolves it or is stale, and note this
  when I claim the issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ilp90/pathreview/commit/57933a87702ae9b0f7742d6be500a27360223d98

**Reproduction summary:**
Ran the issue's two-line repro against my local venv —
`FaithfulnessChecker().check("Knows Python.", [{"text": None}])` — and it raised
`TypeError: sequence item 0: expected str instance, NoneType found` at
`rag/evaluator/faithfulness_checker.py:43`; the existing unit test
`test_none_context_chunk_text` fails with the same traceback (`pytest
tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`).

**PLAN.md link:** https://github.com/ilp90/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** _(optional — not recorded / add Loom link here if you record one)_

**Blockers or open questions:**
Need to confirm whether the referenced PR #211 already fixes #153 (avoid
duplicate work). Also deciding how strictly to handle non-string, non-None chunk
text (coerce with `str(...)` vs. drop to `""`) — leaning conservative. Note: the
same test file has 3 unrelated failing tests that belong to issue #152 (scoring
thresholds), which are out of scope for this fix.
