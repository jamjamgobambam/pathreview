## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluator (rag/evaluator/faithfulness_checker.py)
verifies that AI-generated claims are supported by retrieved context. It builds the
context string with chunk.get("text", ""), but .get() only falls back to the default
when the key is missing — if "text" exists with a value of None, it returns None, and
the " ".join(...) call raises a TypeError. Right now any chunk with a null text field
crashes the whole check instead of being handled. A successful fix treats None text
as an empty string (or skips the chunk) so the checker degrades gracefully, and makes
the failing test test_none_context_chunk_text pass.

**Selection notes:** Tier 1 fits my current familiarity with the codebase — the bug is
isolated to one function, has exact reproduction steps, and an existing failing test
defines "done," so the scope is well-bounded per the "Is this issue right for me?" checklist.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [0c7a92f](https://github.com/nuv2453-ah/pathreview/commit/0c7a92f)

**Reproduction summary:**
Reproduced the issue by running `FaithfulnessChecker().check('Knows Python.', [{'text': None}])` in a local Python shell — confirmed it raises `TypeError: sequence item 0: expected str instance, NoneType found` on line 34 of `rag/evaluator/faithfulness_checker.py`. Also confirmed the failing test `test_none_context_chunk_text` in `make test-unit` shows the same crash.

**PLAN.md link:** [PLAN.md](https://github.com/nuv2453-ah/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to grep for other `.get("text", "")` occurrences in the codebase to check if the same pattern exists elsewhere.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: changed `chunk.get("text", "")` to `chunk.get("text") or ""` in `faithfulness_checker.py`. Confirmed `test_none_context_chunk_text` now passes. Verified no new test failures introduced (52 pre-existing failures, down from 53).

**Next steps:**
Open draft PR on ascherj/pathreview and request peer review via Slack.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/435

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Changed `chunk.get("text", "")` to `chunk.get("text") or ""` in the `context_text` list comprehension inside `FaithfulnessChecker.check()`. This ensures chunks with explicit `"text": None` are treated as empty strings instead of crashing `" ".join()` with a `TypeError`.

**Follow-up investigation:**
Per reviewer feedback, grepped the codebase for other occurrences of the same `.get("text", "")` pattern (the bug: `.get()` only substitutes its default when the key is *missing*, not when the value is explicitly `None`). Found the identical pattern in three other files: `rag/evaluator/relevance_scorer.py`, `rag/retriever/hybrid.py`, and `rag/generator/review_generator.py`. Applied the same `chunk.get("text") or ""` fix to all three for consistency. Verified via `git stash` that pre-existing test failures (62 failed / 366 passed) are identical before and after this change, so no regressions were introduced.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — pre-existing test `test_none_context_chunk_text` now passes; no new failures introduced across the full suite after extending the fix to the 3 additional files.

**Self-review confirmation:** [x] make check passes (3 pre-existing mypy errors in `vector_store.py`, `keyword_search.py`, `output_parser.py` — unrelated to this change, confirmed via `git stash`)  [x] make test-unit passes (62 pre-existing failures unchanged; fix resolves 1)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived. Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a gap in the process.

**How you responded:**
N/A — no feedback to respond to. I requested a peer review in the course Slack channel earlier in the module as required by Week 9, and incorporated my own self-review against CONTRIBUTING.md before finalizing.

---

### Reflection

**What was harder than you expected?**
The bug itself — a one-line fix — was the easy part. What took real time was environment setup: I hit a macOS SSH conflict between my personal GitHub account and my NutriScan work account, since both were trying to use the same default SSH key. I had to set up a `github-personal` SSH alias and rewrite my remote URLs to point through it. That's not something the assignment prepared me for, and it ate a chunk of Week 7 that I expected to spend reading code instead.

**What did you learn about working in a large codebase?**
The biggest shift was realizing that a "small" fix isn't small once you account for its blast radius. `chunk.get("text", "")` looked like an isolated bug in one function, but once I understood the actual failure mode — `.get()`'s default only applies to missing keys, not `None` values — I found the same pattern repeated at three other call sites in the codebase. In my own projects I'd probably have patched the one spot I hit and moved on. Here, I had to think about consistency across the codebase and whether leaving the other three instances would just mean someone else hits the same crash later.

I also learned to take "passing tests" less literally. The codebase had 52 pre-existing failing tests unrelated to my change. In a solo project, a failing test means something's broken and I fix it. In a shared codebase, I had to learn to document what's pre-existing, prove I didn't add to it, and move on — the standard isn't "everything is green," it's "I didn't make it worse."

**How did AI tools help — and where did they fall short?**
AI tools were most useful for fast codebase orientation — pointing me toward where `context_text` was constructed and helping me trace the call sites that shared the same `.get()` pattern. That's the kind of broad-but-shallow search that would've taken me a lot longer to do manually across a codebase I didn't write.

Where it fell short was judgment about scope. AI suggestions on how far to extend the fix (just the one call site vs. all four) weren't reliable on their own — I had to actually read each call site to confirm the fix was appropriate there and wasn't masking a different bug. It was also unreliable for understanding project-specific conventions (commit message format, PR template expectations) — those came from reading CONTRIBUTING.md directly, not from AI suggestions.

**What would you do differently if you started over?**
I'd sort out my Git/SSH setup before claiming an issue, not during Week 7 while trying to also read the codebase for the first time. I'd also start the "search for repeated bug patterns" step earlier — I found the other three call sites somewhat late in the process, and if I'd looked for them right after understanding the root cause, I could've bundled that investigation into my PLAN.md instead of it feeling like a late addition.

**What are you most proud of from this module?**
Catching that the bug wasn't isolated to one line. It would've been easy to submit the minimal one-line diff and call it done — the issue was closed either way — but going back and checking for the same failure mode elsewhere in the codebase felt like the difference between patching a symptom and actually fixing the underlying issue.
