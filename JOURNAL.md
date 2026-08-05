## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/153)

**Issue title:** Faithfulness checker crashes when a context chunk has text: None #153

**Tier:** Tier 1. Since it is my first time contributing I wanted to do an issue that would be easier for me to fix. Additionally I am more experienced in RAG and ingestion compared to some of the other topics on this issue lists(API, Database, etc.), and decided it would be better to work on a issue that I have more experience in. As such I chose this tier 1 issue which focuses on RAG as it covers both my criterias.

**Problem summary:** The issue revolves around the get() function when chunking. get() works but getting the required value, in this case the text or if it does not exists it doesn't crash the program by letting us send a "default" value to insert. However, what if the orignal retrieved value is NONE? In this case, the get() function will recieve the NONE and send that into a join() method which ends up giving an error as it requires the same type(Strings). A succesful fix would be adding a guardrail for this specific case with if statements or the "or" keyword to prevent this issue from occuring, letting the chunker work as it should.

**Branch name:** fix/153-rag-chunk-error

**Setup confirmation:** Yes, App runs locally at localhost:5173

**Cohort ledger:** Yes, Issue added to cohort ledger in row 108

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DineshM4/pathreview/commit/f83a2cf75f614a926b17ca2399c9106f1fc47056

**Reproduction summary:** Ran the minimal repro (FaithfulnessChecker().check('Knows Python.', [{'text': None}])) and the failing test test_none_context_chunk_text against the project venv, both of which raised TypeError: sequence item 0: expected str instance, NoneType found at faithfulness_checker.py:34. This confirmed that chunk.get("text", "") returns None (not the "" default) when the text key is present but null, and " ".join(...) then crashes on the non-string item.

**PLAN.md link:** https://github.com/DineshM4/pathreview/blob/fix/153-rag-chunk-error/PLAN.md

**Blockers or open questions:** None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md. Changed the context concatenation in `rag/evaluator/faithfulness_checker.py` from `chunk.get("text", "")` to `chunk.get("text") or ""`. The `or ""` guardrail coerces an explicitly-null `text` value (`{"text": None}`) to an empty string before `" ".join(...)`, which is the exact case the missing-key default never handled. The previously-failing `test_none_context_chunk_text` now passes.

**Next steps:**
Add one more regression test covering a `None` chunk mixed with valid chunks (to confirm valid text is still used and not just that it avoids crashing), run the full self-review, and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/600

**Branch:** `fix/153-rag-chunk-error`

**What you built:**
A one-line guardrail fix in `FaithfulnessChecker.check()` that stops the faithfulness checker from crashing when a retrieved context chunk has `text: None`. Replacing `chunk.get("text", "")` with `chunk.get("text") or ""` coerces a null text value to an empty string so `" ".join(...)` no longer raises `TypeError: sequence item 0: expected str instance, NoneType found`.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — the existing `test_none_context_chunk_text` (which reproduced the bug) now passes. `test_none_chunk_mixed_with_valid_chunks` now covers a `None` chunk mixed with valid chunks to pass.

**Self-review confirmation:** [x] make check passes (ruff + black clean on the changed file)  [x] make test-unit passes for the target test — note: the repo has ~52 pre-existing unit-test failures in unrelated modules (skill_extractor, tech_detector, structural_chunker) plus 3 pre-existing failures in the scoring-math tests of this file; all were verified to fail on the original code before my change and are outside the scope of issue #153.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

### Reflection

**What was harder than you expected?**
The one-line fix in `rag/evaluator/faithfulness_checker.py:34` was trivial; establishing that it was correct was not. I had to internalize that `dict.get("text", "")` only falls back to `""` on a *missing key*, never on a present-but-null value, so the crash was `" ".join()` receiving `None` rather than anything wrong with the default. Then `make test-unit` surfaced ~52 unrelated failures (skill_extractor, tech_detector, structural_chunker) plus 3 scoring-math failures in my own test file, and I had to re-run them on unmodified `main` to prove they were pre-existing and not mine.

**What did you learn about working in a large codebase?**
In my own projects I'd have normalized every chunk at the boundary or added a schema validator; here the correct move was the smallest diff that closes the issue without changing behavior any other caller depends on. `chunk.get("text") or ""` also silently absorbs `0` and `[]`, which I accepted only because the field is a text string by contract. That kind of "is this coercion safe for this specific field" reasoning only comes from reading the surrounding code, not from the issue text.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation — locating the `join()` call site, drafting the minimal repro `FaithfulnessChecker().check("Knows Python.", [{"text": None}])`, and scaffolding `test_none_chunk_mixed_with_valid_chunks`. Where it fell short was scope judgment: it would happily have "fixed" the unrelated failing modules or widened the change into input validation across the evaluator. Deciding that issue #153 ends at the `None`-to-`""` coercion, and that the other 55 failures were explicitly out of scope, was a call I had to make and defend in the PR.

**What would you do differently if you started over?**
I'd capture a baseline `make test-unit` run on untouched `main` before writing a single line, so pre-existing failures were recorded up front instead of reconstructed afterward. I'd also write the mixed-chunk regression test in the same commit as the repro test, since "doesn't crash" and "still concatenates the valid text" are two different guarantees and I initially only proved the first. Finally I'd open the draft PR earlier to get review in flight rather than finishing everything before asking.

**What are you most proud of from this module?**
The reproduction, not the patch. I pinned the exact failure mechanism — `TypeError: sequence item 0: expected str instance, NoneType found` traced to a null `text` slipping past the `get()` default into `" ".join(...)` — and committed that as a failing test before changing any production code. Because of that, the fix was a one-line consequence of a diagnosis rather than a guess that happened to make a test go green.
