## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `FaithfulnessChecker` builds its context by calling
`chunk.get("text", "")` on each context chunk, assuming this will fall back to
an empty string if text is missing. However, `.get()` only applies its default
when the key itself is absent — if a chunk has `"text": None`, `.get()` returns
`None` instead. This value then gets passed into a `" ".join(...)` call, which
raises a `TypeError` because `join()` expects a list of strings, not `None`.
The fix involves handling the case where `text` is present but `None`, likely
by falling back to an empty string in that case too. This affects the
`rag/evaluator/faithfulness_checker.py` module.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Checklist reasoning ("Is this right for me?"):**

*Part 1 — Understanding the issue:* Yes. The bug is that `check()` calls
`chunk.get("text", "")`, but `.get()` only applies its default when the key
is missing — if a chunk has `"text": None`, `.get()` returns `None` instead
of falling back to `""`. That `None` then gets passed into `" ".join(...)`,
which raises a `TypeError` because `join()` requires a list of strings.
Before the fix: passing a chunk with `text: None` crashes the checker.
After the fix: it should handle `None` the same way it handles a missing
key, treating it as empty text instead of raising.

*Part 2 — Tier fit:* This is my first open-source contribution, and #153
is labeled Tier 1 — a localized, single-method fix in one file. Good match
for where I am right now.

*Part 3 — Codebase readiness:* I opened
`rag/evaluator/faithfulness_checker.py` and read the `check()` method
directly, not just the file listing. I also opened
`tests/unit/test_faithfulness_checker.py` and read through
`test_none_context_chunk_text` (and at least one other test) to see how
the test fixtures and assertions are structured, so I know the pattern
to follow for my own test.

*Part 4 — Scope and time:* I checked the issue comments and the Claims
count in the cohort ledger's Issue Catalog tab before claiming. The fix
itself is small (one conditional or a safer `.get()` pattern), so I'm
confident I can implement, test, and PR it well within the Weeks 8–9
window. There are no "blocked by" references or unresolved dependencies
noted on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/lakshanakolur/pathreview/commit/3739f91

**Reproduction summary:**
Ran `FaithfulnessChecker().check('Knows Python.', [{'text': None}])` locally and
confirmed it raises `TypeError: sequence item 0: expected str instance, NoneType found`,
matching the issue report. Traced it to `chunk.get("text", "")` in `check()`, which only
falls back to `""` when the key is missing — not when the value is explicitly `None`.
Also confirmed the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py` fails the same way, and added a docstring
to it documenting the reproduction.

**PLAN.md link:** https://github.com/lakshanakolur/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** N/A — not recorded this week

**Blockers or open questions:**
Found the same `chunk.get("text", "")` pattern in three other files
(`rag/evaluator/relevance_scorer.py`, `rag/retriever/hybrid.py`,
`rag/generator/review_generator.py`) — same latent bug likely exists there too,
but it's out of scope for #153. Considering whether to flag this as a follow-up
issue after this PR is merged.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for #153: changed `chunk.get("text", "")` to `chunk.get("text") or ""`
in `rag/evaluator/faithfulness_checker.py`, so both a missing `text` key and an explicit
`None` value fall back to an empty string. Completed sub-tasks 1–4 from PLAN.md: located
the exact line, applied the fix, confirmed the target test (`test_none_context_chunk_text`)
and its sibling (`test_missing_text_key_in_chunk`) now pass, and added two additional
edge-case tests (`test_mixed_none_and_valid_context_chunks`,
`test_whitespace_only_context_chunk_text`) to cover scenarios from PLAN.md's edge cases
section. All 4 relevant tests pass.

Ran `make test-unit` and `make check` project-wide to check for regressions. Confirmed
my change introduces zero new test failures and zero new lint errors — the 49 unrelated
test failures and 180 lint errors that show up are pre-existing on `main`, in modules I
never touched (bias_detector, pii_scrubber, review_service, resume_parser, tech_detector,
etc.). The 3 pre-existing failures within `test_faithfulness_checker.py` itself
(`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
`test_multiple_claims_varying_support`) also confirmed to fail identically with or
without my fix — unrelated to the None-handling bug.

**Next steps:**
- Run `make check` locally to confirm formatting/lint on my specific files, and clean up
  anything within scope
- Open a draft PR and request peer/mentor review in Slack
- Address any review feedback
- Write PR description documenting pre-existing failures (drafted, ready to include)
- Finalize and submit PR by Sunday

**Blockers:**
None currently. Note: found the identical `chunk.get("text", "")` pattern in three other
files (`relevance_scorer.py`, `hybrid.py`, `review_generator.py`) — same latent bug likely
exists there, but staying in scope for #153 and considering a follow-up issue instead.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/414

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Fixed a bug in `FaithfulnessChecker.check()` where a context chunk with
`text: None` crashed the checker with a `TypeError`. Changed
`chunk.get("text", "")` to `chunk.get("text") or ""` so both a missing key
and an explicit `None` value are handled gracefully.

**Tests added or updated:**
Updated `tests/unit/test_faithfulness_checker.py`: confirmed
`test_none_context_chunk_text` and `test_missing_text_key_in_chunk` now pass,
and added two new tests — `test_mixed_none_and_valid_context_chunks` and
`test_whitespace_only_context_chunk_text` — for additional edge-case coverage.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both confirmed to introduce no new failures beyond documented pre-existing
ones — see PR description for full details)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback came in — per the Su26 course note, reviewer feedback isn't a live
feature this term, so there was nothing to check for on PR #414 beyond what I
already logged in Week 9 (no comments received on the draft).

**How you responded:**
N/A — no feedback to respond to. If review is enabled in a future term, my
plan would be to treat comments the same way I treated the pre-existing test
failures: verify them against the actual code before agreeing or pushing
back, rather than just deferring to whatever a reviewer says.

---

### Reflection

**What was harder than you expected?**
Getting to the actual one-line fix was fast; getting to the point where I
trusted the fix was the hard part. Because `pathreview` isn't my code, I
couldn't just "know" that `chunk.get("text") or ""` was safe everywhere it
mattered — I had to read through `FaithfulnessChecker` end to end, check how
`check()` gets called elsewhere, and run the full test suite to separate my
change from the 49 pre-existing failures and 180 pre-existing lint errors
already on `main`. Understanding the surrounding system took far longer than
writing the patch itself.

**What did you learn about working in a large codebase?**
In my own projects, if something breaks I usually know which file it's in
because I wrote all of them. Here, tracing a single crash meant reading
across `rag/evaluator/`, `rag/retriever/`, and `rag/generator/` before I was
confident the bug was actually isolated to `faithfulness_checker.py`. That
search also surfaced the exact same `chunk.get("text", "")` pattern in three
other files (`relevance_scorer.py`, `hybrid.py`, `review_generator.py`) — a
reminder that in a large, many-contributor codebase, one reported bug is
often several copies of the same latent bug, and part of the job is deciding
what's in scope for *this* fix versus what belongs in a follow-up issue.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for summarizing — getting oriented quickly in an
unfamiliar file or function, and drafting boilerplate like test scaffolding
and PR description text. They were much less useful for the two things that
actually mattered most: finding the real fault, and reflecting on the work
afterward. Locating the actual root cause (the `.get()` default-vs-`None`
distinction) took manual reproduction and tracing, not a suggestion from a
tool. And writing this reflection honestly required actually having done the
work — a summary tool can't tell me what was hard for me.

**What would you do differently if you started over?**
I'd search the codebase for the bug pattern before implementing the fix
rather than after. I found the three other files with the identical
`chunk.get("text", "")` issue while writing PLAN.md in Week 8, but by then
I'd already scoped the PR to a single file. Doing that grep earlier wouldn't
have changed my fix, but it would have let me decide on the follow-up issue
(and mention it) from the start instead of carrying it as an open question
through Weeks 8 and 9.

**What are you most proud of from this module?**
Understanding the problem well enough to actually trust my own fix — tracing
the bug to its exact cause, confirming it against the existing test, and then
writing two additional edge-case tests (`test_mixed_none_and_valid_context_chunks`,
`test_whitespace_only_context_chunk_text`) beyond what the issue strictly
asked for. Going from "the app crashes" to a fix I could defend with evidence
is the part of this module I'm most proud of, more than the PR itself.