# Module 3 Journal — Ananya

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG evaluation suite's faithfulness checker (`rag/evaluator/faithfulness_checker.py`)
is meant to score how well generated feedback is supported by the retrieved context
chunks. It builds one big context string by joining the `text` field of every chunk.
The bug is that it does this with `chunk.get("text", "")`, and `dict.get`'s default
only applies when the key is *absent* — if a chunk explicitly has `text: None`, `.get`
returns `None`, and `" ".join([... None ...])` then raises a `TypeError`. So any
retrieval result containing a null-text chunk crashes the checker instead of skipping
that chunk. A successful fix would coerce missing/`None` text to an empty string (or
filter such chunks out) so scoring proceeds normally, plus a unit test covering the
`text: None` case.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### "Is this right for me?" — scope reasoning
- **Tier 1 / good first issue:** labeled `tier-1`, `good first issue`, `bug` — appropriate
  for a first contribution to a large codebase.
- **Small, well-bounded blast radius:** the defect is a single line
  (`faithfulness_checker.py:34-36`); the fix is localized and won't ripple across modules.
- **Reproducible & testable:** the failure is a deterministic `TypeError` on a known
  input shape (`{"text": None}`), so it's straightforward to write a regression test.
- **Matches the codebase area I want to learn:** touches the `rag` evaluation code and
  the pytest unit-test layout, which is a good on-ramp to the project's testing patterns.
- **No external services required to reproduce/fix:** the checker is pure Python with no
  DB or API-key dependency, so I can iterate without the full Docker stack.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ananyamk1/pathreview/commit/7f533b777dad3626a09864477a86bef4fd9cc33a

**Reproduction summary:**
Running the existing unit test `test_none_context_chunk_text` against
`FaithfulnessChecker.check` locally raised
`TypeError: sequence item 0: expected str instance, NoneType found` at
`rag/evaluator/faithfulness_checker.py:44`, confirming that a context chunk of
`{"text": None}` crashes the checker because `dict.get("text", "")` returns
`None` (its default only applies to absent keys) and `" ".join([... None ...])`
then fails. I documented the reproduced defect with an inline comment at the
crash site.

**PLAN.md link:** https://github.com/ananyamk1/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Deciding whether the fix should coerce null/missing text to `""` (keeps chunk
count/order, minimal change) or filter such chunks out entirely — leaning toward
coercion plus a `structlog` warning so null chunks don't silently disappear.
Also unsure whether non-string `text` values ever occur in real retrieval
output; the plan handles them defensively regardless.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md. Done so far:
- Sub-task 1 (fix the coercion in `check`): replaced
  `" ".join([chunk.get("text", "") ...])` in
  `rag/evaluator/faithfulness_checker.py` with a loop that keeps non-empty
  string texts, skips `None`/empty values (logging a `structlog` count), and
  `str()`-coerces any non-string value.
- Sub-task 2 (guard the return path): confirmed an all-`None`/empty context now
  returns a valid `0.0` instead of raising.
- Sub-task 3 (turn the None test green) and sub-task 4 (regression coverage):
  rewrote `test_none_context_chunk_text` as an explicit `#153` regression test
  and added `test_mixed_none_and_valid_chunks`, `test_all_none_chunks_returns_zero`,
  `test_empty_string_text_chunk`, and `test_non_string_text_is_coerced` in
  `tests/unit/test_faithfulness_checker.py`.

**Next steps:**
Sub-task 5 — run the full suite + linters, self-review against
`docs/CONTRIBUTING.md`, then open the PR and request feedback in the cohort
Slack channel.

**Blockers:**
The repo has ~53 pre-existing unit-test failures and ~181 pre-existing lint
errors unrelated to issue #153 (e.g. `test_skill_extractor.py`,
`test_tech_detector.py`, and 3 pre-existing faithfulness scoring-threshold
tests). I baselined these before starting so I can show my change introduces no
new failures; not a blocker for the fix itself.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/462

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
`FaithfulnessChecker.check` crashed with
`TypeError: sequence item 0: expected str instance, NoneType found` whenever a
retrieved context chunk was `{"text": None}`, because `dict.get`'s default only
applies to absent keys. The fix coerces each chunk's text to a string —
skipping `None`/empty values and `str()`-coercing non-strings — so faithfulness
scoring proceeds over whatever valid text remains instead of aborting on one
null chunk.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — rewrote `test_none_context_chunk_text`
as an explicit regression test for the `#153` `TypeError`, and added four tests:
`test_mixed_none_and_valid_chunks` (a `None` chunk is skipped while a valid chunk
still supports the claim), `test_all_none_chunks_returns_zero` (all-`None` context
returns `0.0`), `test_empty_string_text_chunk` (empty-string text is no-support,
not a crash), and `test_non_string_text_is_coerced` (a numeric `text` is coerced,
not crashed).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Interpreted per the assignment's pre-existing-failures rule: the repo has
~53 pre-existing unit-test failures and ~181 pre-existing lint errors unrelated
to #153. Baselined before my change and re-checked after — my change introduces
no new failures. My two touched files pass `ruff`, `black`, and `mypy`
individually. Details in the PR's "Notes for Reviewers".)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review arrived. PR #462 (https://github.com/ascherj/pathreview/pull/462) has
been open since the end of Week 9 with no comments, review requests answered, or
maintainer activity on the thread. I re-checked the PR at the end of Week 10 and
it is still open and unreviewed. Per the Summer 2026 note, reviewer feedback
isn't part of this term, so this is the expected outcome rather than a stalled
conversation.

**How you responded:**
Nothing to respond to, so I left the branch as submitted rather than adding
speculative commits on top of a PR nobody has read yet. The one thing I did do
was re-read my own diff and the PR description as if I were the reviewer, to
check that the two questions I'd expect a maintainer to ask are already answered
in writing: (1) why coerce `None` text to skipped-and-counted instead of
filtering the chunk out silently — answered in the code comment and the
`structlog` `faithfulness_skipped_empty_chunks` line; and (2) whether the
~53 unit-test failures and ~181 lint errors in the PR's CI are mine — answered
in the "Notes for Reviewers" section, where I baselined them before touching
anything. If feedback does come in later I'd work the threads in the order the
guide describes: read everything first, then reply to each comment before
pushing follow-up commits.

---

### Reflection

**What was harder than you expected?**
The one-line part of the fix was the easy part; the hard part was deciding what
"correct" meant. Issue #153 says the checker crashes on `{"text": None}`, but it
doesn't say what should happen instead, and there are at least three defensible
answers: coerce to `""`, drop the chunk from the list, or raise a clearer error
for the caller. I spent most of Week 8 on that decision rather than on code, and
I ended up on coerce-and-count-skips because the checker returns a ratio —
dropping chunks silently would quietly change a score, which is worse than
crashing, since nobody would notice. I also didn't expect the *baseline* to be
so much work: the first time I ran `make test-unit` I got a wall of red and
assumed I'd broken the environment, when in fact ~53 of those failures were
already there on a clean checkout. Proving "not mine" took longer than the fix.

**What did you learn about working in a large codebase?**
In my own projects I know the whole call graph, so I can reason about a change
from memory. Here I couldn't — `FaithfulnessChecker.check` is called from the
RAG evaluation path, and I had no idea who constructs those `context_chunks`
dicts or whether a `text: None` chunk was a real upstream bug or a legitimate
shape I had to tolerate. That changed how I wrote the fix: instead of asserting
what the data should look like, I made the function survive whatever it gets and
log when the input is odd. I also learned that a repo's existing conventions
carry more weight than my preferences — `structlog` with event-name-plus-kwargs
(`logger.info("faithfulness_skipped_empty_chunks", skipped_count=skipped)`) is
not how I'd log by instinct, but matching the file's five other log calls
matters more than my taste, because the reviewer's job is to read a diff that
looks like the rest of the code.

**How did AI tools help — and where did they fall short?**
Most useful for orientation and for mechanical breadth. Asking for the places a
`dict.get(key, default)` idiom breaks got me to the real root cause — the
default only applies when the key is *absent* — faster than I'd have found it by
staring at the traceback, and it was good at generating the extra test cases
around the core one (`test_mixed_none_and_valid_chunks`,
`test_all_none_chunks_returns_zero`, `test_empty_string_text_chunk`,
`test_non_string_text_is_coerced`). Where it fell short was exactly the judgment
call above: asked what to do about `text: None`, it happily produced a confident
answer for whichever option I hinted at, including the silent-filter version
that would have corrupted the score. It has no stake in the project, so it can't
tell me which tradeoff this codebase would accept — that came from reading how
`check` uses `supported / len(claims)` and realizing the denominator makes
silence dangerous. It also couldn't tell me which of the 53 failing tests were
pre-existing; only actually running the suite on a clean checkout could.

**What would you do differently if you started over?**
Two things. First, I'd baseline the test suite and linters on a clean checkout
*before* writing a single line, and paste that baseline into PLAN.md on day one —
I did it eventually, but reconstructing it after the fact made me less sure of my
own results and cost me a Week 9 check-in's worth of time. Second, I'd ask the
maintainer the scope question early, in the issue thread, rather than resolving
it alone in PLAN.md: "should a null-text chunk be skipped or should the caller
hear about it?" is a 30-second answer for someone who knows the retrieval code,
and asking in public would also have put my name on the issue before I opened a
PR out of nowhere. I'd probably also pick an issue whose file wasn't sitting next
to a set of already-failing tests, since half my PR description ended up being
about noise I didn't cause.

**What are you most proud of from this module?**
That the commit message explains the *why* rather than the change. Anyone reading
`git log` later sees "dict.get's default only applies when the key is absent" and
learns the actual Python gotcha, not just that a line moved — and the code
comment at the fix site says the same thing so the next person doesn't
"simplify" it back into the bug. The fix itself is 21 lines; the part I care
about is that it's self-documenting and that the regression test names the issue
number, so `#153` can't silently come back.
