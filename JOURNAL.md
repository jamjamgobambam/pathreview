# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluation layer scores how well generated
feedback is supported by the retrieved context chunks. To do that, it stitches
all the chunk text together with `" ".join([chunk.get("text", "") ...])`. The
bug is that `dict.get("text", "")` only falls back to the empty string when the
key is *absent* — if a chunk actually contains `{"text": None}`, `.get()` returns
`None`, and joining a list that contains `None` raises
`TypeError: sequence item 0: expected str instance, NoneType found`. So any
review whose retrieval produces a chunk with a null text field crashes the whole
faithfulness check instead of just skipping that chunk. A successful fix makes
the checker treat a `None` text value the same as an empty/missing one (coerce to
`""` or filter it out) so scoring proceeds normally, and turns the existing
`test_none_context_chunk_text` case in `tests/unit/test_faithfulness_checker.py`
from failing to passing. This lives in `rag/evaluator/faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-chunk-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope reasoning

- **Do I understand what's broken?** Yes. I reproduced the failure path by reading
  the code: `faithfulness_checker.py:34-36` uses `chunk.get("text", "")`, which
  does not guard against an explicit `None` value, and the downstream `" ".join`
  is what raises the `TypeError`.
- **Is the scope contained?** Yes — the fix is a one-file change in
  `rag/evaluator/faithfulness_checker.py`, with a matching test already named in
  the issue (`test_none_context_chunk_text`). No API, schema, or frontend changes.
- **Is there a clear definition of done?** Yes — the crash is replaced by graceful
  handling of `None`/missing text, and the referenced unit test passes.
- **Is the effort realistic for a Tier 1 first contribution?** Yes — it's a
  well-understood defensive-coding bug with an existing failing test to validate
  against, no external API dependency in the code path being fixed.
- **Risks / unknowns:** Need to confirm the intended behavior is "coerce to empty"
  vs. "drop the chunk entirely" — both keep scoring alive; I'll match whatever the
  existing test asserts.
