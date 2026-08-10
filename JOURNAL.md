## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The `FaithfulnessChecker().check()` method builds context string by joining the "text" field from each context chank. The issue is that when chank's "text" set to `None`, `.get("text", "")` returns `None` instead of default and crash the code with `TypeError` message by joining to `None`. This bug affects on faithfullness-checking logic in `tests/unit/test_faithfulness_checker.py` where `test_none_context_chunk_text()` method fails because `.check()` not handled this case. The successful outcome would be to make context-building step treat "text" value set to `None` in same way as empty or missing one, so that checker can score feedback correctly even if chunk's input is distorted.

**Selection notes ("Is this right for me?" checklist):**

- **Understanding:** I can descrive this issue in such way: `check()` builds a context string from chunk using `chunk.get("text", "")`, but this only defaults when the key is "missing". If "text" is present and would be set to `None` then `.get()` returns `None`, and the later `" ".join(...)` call would crash the code with `TypeError` message.
- **Affected area:** The issue is in `FaithfulnessChecker.check()`. The failing test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` confirms it.
- **Definition of done:** Before the fix: passing a chunk like `{"text": None}` crashes with a `TypeError` message. After the fix: `check()` should treat that chunk's text as empty or missing one and still return a correct score feedback.
- **Tier fit:** This is a Tier 1 issue because it requires one or two line fix that isolated to a single method, fully covered by an existing test and with no cross-module dependencies. This is my first contribution to a large codebase, which is why Tier 1 would be my starting point.
- **Codebase readiness:** I've located `check()` through `tests/unit/test_faithfulness_checker.py` and the surrounding context-building logic, and read `test_none_context_chunk_text` from start to finish in the test file.
- **Scope/time:** Based on the issue, I estimate 3-6 hours (Tier 1 estimate for Week 8-9) since it looks look like a 1-2 line fix with verifying the existing test passes.
- **Blockers:** No open blockers or dependencies are noted in the issue.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/7e4a2dbf591dc0453c592645c05d158f53ba52e1

**Reproduction summary:**

Ran `pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v` and confirmed that test fails with `TypeError` message: `sequence item 0: expected str instance, NoneType found` that was raised when `.check()` tries to join chunk's `None` "text" value into the context
string.

**PLAN.md link:** https://github.com/DanyloBatrak/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**

Uncertain for the one instruction:

`Request peer or mentor feedback on a draft PR` :

Where do I get PR link and how do I need to contact to instructor. Do I need to choose own instructor or I need to choose certain instructor

## Week 9 — Solution building & PR submission

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/666#issue-5046789813

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**

Fixed a bug in `FaithfulnessChecker.check()` where context chunks with a `None` value for `"text"` caused a `TypeError` during string concatenation, since `.get("text", "")` only uses the default value when the "text" key is missing, but not when key exists and its value equals to `None`. Changed the pattern to `.get("text") or ""` so missing, `None`, and empty text are all treated consistently as empty strings.

**Tests added or updated:**

Verified `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` now passes, covering context chunks with `{"text": None}.`

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
(Note: Both checks pass according to the project's pre-existing failures policy. My changes introduced no new failures. `ruff check` on the modified file passes with no errors. Baseline `make test-unit` had 53 failures, after my fix - 52 failures, with the only change being `test_none_context_chunk_text` changing from failed to passed.)

**Draft PR feedback received from:** none (yet to be reviewed)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [X] No — still awaiting review

**Summary of feedback:**

No review came in

**How you responded:**

---

### Reflection

**What was harder than you expected?**

Finding out the part where `.get("text", "")` doesn't work with the `None` case took much longer than expected to be for Tier 1 because the default-value argument in `chunk.get()` only activates when the key is missing, not when text set to `None` value. That distinction is easy to miss when scanning code, and it's the kind of bug that only shows with a specific data shape (e.g. a chunk that has a `"text"` key but no content), which is the reason why it slipped through originally.

**What did you learn about working in a large codebase?**

I learned that this codebase had 53 pre-existing failing tests and 181 pre-existing lint errors across the codebase which are been not related to my changes.When I first joined to this project, I thought that this codebase would have a clean baseline. However, I now understand that when I woek in shared codebase I would have to separate "failure that I caused" from "failure that were already there".

This meant that by running `make test-unit` I need to check result before and after I did change rather than to just checking if my one new test passed.

**How did AI tools help — and where did they fall short?**

AI was most useful when I had hard time to with running tests and in explaining the difference between `chunk.get()` default value and the "or" fallbacks. However, it fall short when it came to telling me which of 53 failing tests were safe to ignore and what are related to my change. Because of that I had to read the test output and issue tracker by myself to find exact issue that related to my change.

**What would you do differently if you started over?**

If I started over, I would run the full baseline test before I touch any code rather than after I make the fix, so that I had a clear view of how many tests and lint errors were failling from the beginning. That way I could see the difference from the start instead of rebuilding it later.

**What are you most proud of from this module?**

I most pround of that, while working on Tier 1 problem I improved my project management skills. I noticed three other failling tests in same file that looked related to my fix. I investigated them and confirmed that they are not related to my fix. Instead of fixing them umpropted or ignoring them completely, I called them out in my PR as "pre-existing failing tests in `test_faithfulness_checker.py`." This taught me of importance of staying on track while still documenting other issues I discovered along the way.
