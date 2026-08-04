## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/159]

**Issue title:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide
 #159]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]
### summary
Not sure excatly but I know its about logging. The issue break down talks about pytest and failures. I am guessing thats what they are looking to fix is structlog working with pytest.


**Branch name:** [fix/159-structlog-output-issue-with-pytest]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/duhnk/pathreview/commit/61e3d73d48801b7263dc33e4f86149e25c12faef]

**Reproduction summary:**
Ran `pytest tests/unit/test_batch_processor.py`. The test
`test_empty_chunks_list_returns_empty` fails: the warning "Empty chunks list
provided to BatchEmbeddingProcessor" clearly appears in pytest's *Captured
stdout*, but `caplog.text` is empty and `caplog.records` is empty, so the log
assertion fails even though the log line was actually emitted.

**Root cause (my current understanding):**
structlog is emitting the log through its own renderer/output (the line lands on
stdout with structlog's `ConsoleRenderer` format), but it is not being routed
through the standard-library `logging` handlers that pytest's `caplog` fixture
hooks into. Because `caplog` only captures records that flow through stdlib
`logging`, structlog output bypasses it entirely — which is why this breaks any
test suite-wide that asserts on logs via `caplog`. See `core/logging.py`
(`configure_logging` / `get_logger`) for the structlog setup.

**Fix direction (to confirm in Week 9):** wire structlog into stdlib logging so
records propagate to `caplog` (e.g. a shared test fixture/conftest that
configures `structlog.stdlib.ProcessorFormatter` / `wrap_for_formatter`), or give
tests a structlog-native capture helper (`structlog.testing.capture_logs`) and
update the assertions. Decide which approach before implementing.

**PLAN.md link:** [NOTE: the current PLAN.md documents a *different* bug (resume
upload), not issue #159. Needs to be rewritten (or a separate plan added) for
#159 before pasting a link here.]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
- Which fix approach the maintainers prefer: routing structlog through stdlib
  logging (keeps `caplog` working) vs. switching tests to
  `structlog.testing.capture_logs`.
- Whether the fix should touch the global logging config in `core/logging.py`
  (affects production output) or be isolated to the test harness only.


  ## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

**Next steps:**
[What are you working on for the rest of the week?]

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]
fix/159-structlog-output-issue-with-pytest
**What you built:**
Added an autouse pytest fixture in `tests/conftest.py` that reconfigures
structlog to log through Python's standard-library `logging`
(`structlog.stdlib.LoggerFactory`) instead of its default `PrintLogger`, which
had been writing straight to stdout and bypassing the handlers `caplog` installs.
With records now flowing through stdlib logging, `caplog.records` / `caplog.text`
capture them, so log assertions work suite-wide. The fix is isolated to the test
harness and leaves production logging behaviour unchanged.

**Tests added or updated:**
Added `tests/unit/test_logging_caplog.py` covering warning capture, info capture
via `caplog.set_level`, and rendering of bound key/value context. The
pre-existing `tests/unit/test_batch_processor.py::test_empty_chunks_list_returns_empty`
now passes unmodified; the full unit suite went from 377 to 378 passing with zero
regressions (verified by diffing the failure set before/after).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
Honest status: my changes are ruff- and black-clean and add no new mypy errors,
but repo-wide `make check` (mypy) and `make test-unit` still report failures that
**pre-date this branch** and are unrelated to #159 — 52 pre-existing failing
tests, plus mypy typing debt (missing third-party stubs, untyped legacy code).
So neither box is ticked for the repo as a whole, though the #159 change itself
passes all three checks.

**Draft PR feedback received from:** [name or Slack handle, or "none"]