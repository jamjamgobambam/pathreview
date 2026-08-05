## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `rag/evaluator/faithfulness_checker.py` builds
its context by calling `chunk.get("text", "")` on each context chunk,
assuming this will always yield a string. However, `.get()`'s default
value only kicks in when the key is missing entirely - if a chunk
dictionary has the key `"text"` present but explicitly set to `None`,
`.get()` returns `None` instead of the default empty string. This
`None` then gets passed into `" ".join(...)`, which raises a
`TypeError` since `join` expects a list of strings. A successful fix
will make the checker handle `None` values gracefully (coercing them
to empty strings before joining) so it can process context chunks
with missing or null text without crashing.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope-fit reasoning:**
I worked through the "Is this right for me?" checklist before claiming this issue.

- *Understanding the issue:* I can restate the bug without re-reading it -
  `check()` builds context via `chunk.get("text", "")`, but `.get()`'s default
  only applies when a key is missing, not when it's present with value `None`.
  A chunk with `{"text": None}` causes `" ".join(...)` to raise `TypeError`.
  "Done" means the checker returns a valid score instead of crashing when
  `text` is `None`.

- *Tier fit:* This is my first contribution to a codebase this size, so Tier 1
  is the right level - the fix is isolated to one function in one file and
  doesn't require understanding how the RAG pipeline fits together end to end.

- *Codebase readiness:* I located and read `check()` in
  `rag/evaluator/faithfulness_checker.py`, including the surrounding context
  needed to understand how chunks flow into the join call. I also read
  `tests/unit/test_faithfulness_checker.py` end to end, including
  `test_none_context_chunk_text` (text present but `None`) and the adjacent
  `test_missing_text_key_in_chunk` (text key missing entirely) - these are
  separate tests because they exercise different code paths even though both
  expect the checker to return a valid float score rather than crash.

- *Scope and time:* I checked the issue comments and the cohort ledger's
  Claims count for #153 and I'm comfortable with how many others are on it.
  This is a small, contained fix with a repro and existing tests already
  defined, so I estimate 3-6 hours of focused work is realistic within
  Weeks 8-9. There are no blockers or dependencies noted on the issue.


  ## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/Clearxheaded/pathreview/commit/5c8e0fd5e726ecdd0b598c0f3e9521f900a91e8a

**Reproduction summary:**
I reproduced the bug by calling `FaithfulnessChecker().check('Knows Python.', [{'text': None}])`
directly, which raised `TypeError: sequence item 0: expected str instance,
NoneType found` at the `" ".join(...)` call in `check()`. I also ran the
existing test suite and confirmed `test_none_context_chunk_text` fails with
the same error, while the adjacent `test_missing_text_key_in_chunk` already
passes - confirming the bug is specific to a `None` value, not a missing key.

**PLAN.md link:** https://github.com/Clearxheaded/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
None currently. Still deciding whether to search for similar `.get("text", ...)`
patterns elsewhere in the codebase during implementation, or keep scope
strictly limited to this one file for the Tier 1 fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #153: changed `chunk.get("text", "")` to
`chunk.get("text") or ""` in `rag/evaluator/faithfulness_checker.py` so that
both a missing `"text"` key and a present-but-`None` value are handled
gracefully. Confirmed `test_none_context_chunk_text` and
`test_missing_text_key_in_chunk` both pass. Ran the full test file (22 tests)
and confirmed 3 pre-existing failures are unrelated to this change (verified
identical before/after via `git stash`). Ran `ruff`, `black`, and `mypy`
scoped to the changed file - all pass. Opened a draft PR:
https://github.com/ascherj/pathreview/pull/846

**Next steps:**
Share the draft PR in Slack for peer/mentor feedback, address any feedback
received, then mark the PR ready for review and complete Check-in 2.

**Blockers:**
None currently.

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No reviewer feedback was available this term (reviewer feedback is not a
feature in Summer 2026, per the course note).

**How you responded:**
N/A - no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Environment setup took far longer than I expected, and it wasn't the code
that was hard, it was the local infrastructure. I hit a real Docker port
conflict from leftover containers from other projects that silently
prevented `docker compose up -d` from starting anything, with no obvious
error message pointing to the cause. 

**What did you learn about working in a large codebase?**
The habit that mattered most wasn't reading code faster, it was verifying
assumptions before acting on them. When I hit test failures after my fix, I
didn't just assume my change broke something; I used `git stash` to compare
before/after and confirmed the failures were pre-existing and unrelated.
I also learned that a fix which looks like a one-line change still requires understanding the whole function's
contract (what should `check()` return in every case?) and checking whether
the same buggy pattern exists elsewhere in the codebase, even if I choose
not to fix those instances now.

**How did AI tools help - and where did they fall short?**
AI assistance was most useful for methodically working through infrastructure
failures - reading long stack traces, Docker logs, and pytest output and
narrowing down what actually mattered versus what was noise (like the
harmless `docker-compose.yml` version warning or the bcrypt version-reading
warning during seeding). It was also useful for keeping the documentation
work (JOURNAL.md, PLAN.md, PR description) structured and consistent with
what each week's rubric actually asked for. Where it fell short: it couldn't
run my Docker containers or see my actual file state - I still had to run
every command myself, paste back real output, and correct course when the
file wasn't what we expected (like the empty JOURNAL.md commit, or the
encoding issue with the em dash). The actual verification - does this test
pass, is this the right branch, did this file save correctly - always had
to come from me actually running things, not from assuming the AI's
suggestion worked.

**What would you do differently if you started over?**
I'd budget significantly more time for environment setup up front, and I'd
run `docker ps -a` and `docker compose ps` earlier to check for leftover
containers from other projects before assuming a fresh `docker compose up`
would just work. I'd also fix editor/encoding settings (UTF-8) before
writing my first JOURNAL.md entry instead of fighting garbled em dashes
after the fact.

**What are you most proud of from this module?**
Catching that my fix didn't break the three already-failing tests, by
actually stashing my change and re-running instead of just assuming. Sounds
small, but that's the exact kind of check that separates "believes their fix
is safe" from "confirmed their fix is safe" - and it made my PR description
something I could stand behind with evidence instead of hope.