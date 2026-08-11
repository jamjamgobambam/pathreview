# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method in `rag/evaluator/faithfulness_checker.py` builds a single context string by joining the `text` field from each retrieved context chunk, falling back to `""` when a chunk has no `text` key. The bug is that `dict.get("text", "")` only applies its default when the key is *missing* — if a chunk explicitly has `text: None`, `.get()` returns `None` instead of an empty string, and passing that into `" ".join(...)` raises a `TypeError`. This affects the RAG evaluation pipeline, which is used to score how well generated feedback is supported by retrieved context. A successful fix would treat a `None` text value the same as a missing one (i.e., normalize it to `""` before joining) so the checker degrades gracefully instead of crashing, and would make the existing `test_none_context_chunk_text` test pass.

**Branch name:** 153-RAGfaithfulnessCHecker

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Local reproduction notes

Reproduced locally by invoking the faithfulness checker with a context chunk whose text field is explicitly `None`:

```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker

checker = FaithfulnessChecker()
checker.check("Has Python skills", [{"text": None}])
```

Observed behavior: the code reaches the context join step and raises `TypeError: sequence item 0: expected str instance, NoneType found` because `None` is not normalized to `""` before joining.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** <https://github.com/Bijay-Thakur/pathreview/commit/e8b421c143ef52ad33433b45b3dd324e9fef8a69>

**Reproduction summary:**
Reproduced by calling `FaithfulnessChecker().check("Has Python skills", [{"text": None}])` directly, which raises `TypeError: sequence item 0: expected str instance, NoneType found` at the `" ".join(...)` step, since `chunk.get("text", "")` returns `None` (not the default) when the key exists but is explicitly `None`.

**PLAN.md link:** <https://github.com/Bijay-Thakur/pathreview/blob/153-RAGfaithfulnessCHecker/PLAN.md>

**Walkthrough video (recommended):** <https://www.loom.com/share/4765631dfa014718a4bde88d5904fd3b>

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `rag/evaluator/faithfulness_checker.py`: the context-join step now uses `chunk.get("text") or ""` instead of `chunk.get("text", "")`, so an explicit `text: None` is normalized to an empty string instead of crashing the `" ".join(...)` call. The existing regression test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` now passes. Ran the full unit suite to confirm no regressions — the only other failures in that test file (partial/multi-chunk scoring tests) are pre-existing and unrelated to this bug, confirmed by checking them against the pre-fix baseline. All sub-tasks from PLAN.md are complete.

**Next steps:**
Finish self-review against `docs/CONTRIBUTING.md` conventions, open the PR, and fill out the PR template.

**Blockers:**
None. Local environment was missing dependencies (`structlog` and other project extras) needed to run the test suite; resolved by installing them.

---

### Check-in 2 (end of week)

**PR link:** <https://github.com/ascherj/pathreview/pull/994>

**Branch:** `153-RAGfaithfulnessCHecker`

**What you built:**
Fixed a crash in `FaithfulnessChecker.check()` where a context chunk with an explicit `text: None` value raised a `TypeError`. Changed `chunk.get("text", "")` to `chunk.get("text") or ""` when concatenating context chunk text, since `.get()`'s default only applies when the key is missing, not when it's present but `None`.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the regression test `test_none_context_chunk_text` already existed for this case and now passes; no new test was needed since it was already in place but failing before the fix.

**Self-review confirmation:** [x] make check passes (scoped to the touched file — repo-wide lint/format debt is pre-existing and unrelated)  [x] make test-unit passes (target test now passes; other pre-existing failures elsewhere in the suite are unrelated to this change)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
PR #994 is still open with no reviews submitted as of this writing. No comments, requested changes, or approvals have come in.

**How you responded:**
N/A — nothing to respond to yet. If feedback arrives after this journal is finalized, I'll address it directly on the PR thread rather than back-editing this entry, since the point of this journal is to capture the process as it actually happened.

---

### Reflection

**What was harder than you expected?**
The fix itself was one line, but everything around the fix took longer than I assumed it would going in. Just getting the test suite to run locally required installing `structlog` and a handful of other project extras that weren't obvious from a first read of `README.md` — the kind of environment friction that's invisible until you actually try to execute someone else's code. I also underestimated how much time goes into confirming a fix is *safe*, not just correct: after the change, I had to run the full unit suite, notice the pre-existing unrelated failures in the same test file, and go back to a pre-fix baseline to confirm those failures weren't something I'd introduced. That verification step — proving a negative — took longer than writing the fix.

**What did you learn about working in a large codebase?**
The regression test (`test_none_context_chunk_text`) already existed in the suite before I touched anything — someone had written it in anticipation of this exact bug, and it was just sitting there failing. That's very different from a personal project, where tests only exist if I wrote them. It taught me to search for existing tests *before* writing new ones, and to treat a failing pre-existing test as a spec for the fix rather than something to design from scratch. I also learned to scope changes narrowly: the bug (`dict.get(key, default)` not applying its default when the key is present but `None`) could plausibly exist in other evaluator paths in the codebase, but PLAN.md explicitly called that out as a risk and I deliberately left it alone rather than "fixing" code nobody asked me to touch. In a codebase I don't own, minimal blast radius matters more than completeness.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, verifiable parts of the loop: writing the reproduction snippet, tracing through `FaithfulnessChecker.check()` to confirm exactly where the `TypeError` originated, and drafting the PLAN.md structure. It was fast at pattern-matching "this is a `.get()` default footgun" once I pointed it at the traceback. Where it fell short was judgment calls that depend on context outside the diff — whether the pre-existing test failures elsewhere in the file were safe to ignore, whether other evaluator paths needed the same fix, how narrowly to scope the change per this specific repo's conventions in `docs/CONTRIBUTING.md`. Those required actually reading the surrounding code and the maintainers' stated expectations, not just pattern-matching the bug.

**What would you do differently if you started over?**
I'd set up the local dev environment (installing all extras, running the full test suite once) in Week 7 before selecting an issue, instead of discovering the missing dependencies mid-fix in Week 9. It would have removed a whole category of friction from the middle of the cycle. I'd also try to get eyes on the PR earlier — opening it as a draft sooner and pinging for early feedback, rather than treating review as something that happens only after the implementation feels "done."

**What are you most proud of from this module?**
Catching that the bug was specifically about `.get()`'s default-value semantics — not "the code doesn't handle `None`" in some vague sense, but the precise mechanism (`.get(key, default)` only substitutes when the key is *absent*, not when it's present and `None`). Being able to name the exact behavior instead of just patching around a stack trace is what let the fix stay a one-line change instead of turning into a bigger, sloppier defensive-coding pass.
