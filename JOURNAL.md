## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker verifies that generated claims are actually supported
by the retrieved context, but it crashes when a context chunk has `None` as
its text value instead of an empty string. The code uses
`chunk.get("text", "")` to build the combined context string, which only
falls back to the default when the "text" key is missing entirely — if the
key exists but is explicitly `None`, `.get()` returns `None`, and joining a
list containing `None` with a string raises a TypeError. This affects the
`rag` module's faithfulness-scoring logic, and the fix would involve safely
coercing a `None` text value to an empty string before concatenation.

**Branch name:** fix/153-faithfulness-checker-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger 



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ReevaSharma/pathreview/commit/3f8f6c0

**Reproduction summary:** Ran `FaithfulnessChecker().check('Knows Python.',
[{'text': None}])` locally and confirmed it raises `TypeError: sequence
item 0: expected str instance, NoneType found`, matching the issue. Also
confirmed `test_none_context_chunk_text` in the existing test suite
currently fails with the same error.

**PLAN.md link:** https://github.com/ReevaSharma/pathreview/blob/fix/153-faithfulness-checker-none-text-crash/PLAN.md

**Blockers or open questions:**
None currently — the fix is a small, well-scoped one-line change.



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented the fix in `faithfulness_checker.py` —
changed `chunk.get("text", "")` to `chunk.get("text") or ""` so that a
`None` value is treated the same as a missing key. Confirmed the
previously-failing `test_none_context_chunk_text` now passes, and
`make test-unit` shows 52 failed / 376 passed (down from the 53/375
baseline), confirming no new regressions were introduced.

**Next steps:** Run `make check` to confirm no new lint issues in the
touched file, self-review against CONTRIBUTING.md, open a draft PR for
feedback, then finalize the PR description and submit.

**Blockers:** None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/801

**Branch:** fix/153-faithfulness-checker-none-text-crash

**What you built:** Fixed a crash in `FaithfulnessChecker.check()` where a
context chunk with `text: None` caused a `TypeError` when building the
combined context string. Changed `chunk.get("text", "")` to
`chunk.get("text") or ""` so that both a missing key and an explicit
`None` value are treated as an empty string.

**Tests added or updated:** No new test file was needed — the existing
test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py`
already covered this exact scenario. It was failing before the fix and
passes after it.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both confirmed to introduce no new failures beyond the documented
pre-existing baseline of 53 test failures / 182 lint errors, unrelated to
issue #153 — see PR description for details)

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:** No reviewer feedback arrived on PR #801 by the
end of the module. Per the Su26 note, reviewer feedback isn't a feature
this term.

**How you responded:** N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Confirming the pre-existing baseline was more involved than I expected.
Before touching any code, `make test-unit` showed 53 failing tests and
`make check` showed 182 lint errors across the codebase, almost entirely
unrelated to my issue. It would have been easy to assume something was
wrong with my setup, but the real work was carefully separating "failures
that already existed" from "failures I might have caused" — running the
full suite before and after my change and diffing the counts, not just
trusting a single passing test in isolation.

**What did you learn about working in a large codebase?**
A one-line bug fix touches more than one line of process. The actual code
change — `chunk.get("text", "")` to `chunk.get("text") or ""` — took
minutes. Documenting it, tracing it to the exact root cause (`dict.get()`'s
default only applies to missing keys, not `None` values), confirming it
against the existing test suite, and writing up the pre-existing-failures
context for reviewers took much longer. In a codebase you don't own, the
explanation and the evidence trail matter as much as the fix itself,
because a reviewer has to trust your change didn't break something they
can't see from the diff alone.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation — quickly understanding what
`FaithfulnessChecker.check()` and its surrounding test file were doing,
and for double-checking my PLAN.md's risk section before I finalized it.
It fell short on judgment calls that needed the actual codebase in front
of me: deciding whether the three other failing tests in
`test_faithfulness_checker.py` were related to my change (they weren't,
but I had to actually read the failure output and the `_is_supported`
logic to be sure) and deciding exactly how to phrase the pre-existing-failures
section of the PR description so it was honest without sounding like I
was making excuses.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` for the baseline in Week 7,
before writing PLAN.md, rather than waiting until Week 9. Having the exact
pre-existing failure count early would have let me write a sharper "Risks
& unknowns" section from the start, instead of discovering the scope of
pre-existing issues later.

**What are you most proud of from this module?**
Catching that the three other `test_faithfulness_checker.py` failures were
pre-existing and unrelated, rather than assuming my fix caused them. It
would have been easy to either panic and try to fix all four failures, or
to not notice the distinction at all. Running the full suite before and
after, and reading each failure's actual assertion rather than just its
name, is the habit I'm most glad I built this module.