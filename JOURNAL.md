## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This project logs through structlog, configured once in `core/logging.py`.
Any test that wants to assert something was logged uses pytest's built-in
`caplog` fixture — but `caplog` captures nothing, so every log-based assertion
fails across the whole test suite. The cause is in `configure_logging()`: the
processor chain ends in `ConsoleRenderer`/`JSONRenderer`, which turns each event
into a finished string *before* it reaches the standard-library logging pipeline,
and `cache_logger_on_first_use=True` freezes the logger so the handler `caplog`
attaches per-test is never used. A successful fix routes structlog records through
stdlib logging in a way `caplog` can see (for example a `ProcessorFormatter`-based
setup plus a test fixture in `tests/conftest.py` that reconfigures structlog and
disables caching during tests), so log assertions pass suite-wide again without
changing how logs look in dev/production.

**Branch name:** fix/159-structlog-pytest-caplog

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
<!-- To do: comment on issue #159 to claim it, then add name + GitHub username +
     issue # to the Section 1B tab of the cohort ledger. -->

---

### "Is this right for me?" — scope reasoning

- **Tier fit:** Tier 1, labeled `good first issue`. Appropriate for a first
  contribution to this codebase.
- **Scope is contained:** the change centers on logging configuration
  (`core/logging.py`) plus a shared test fixture (`tests/conftest.py`). No
  product feature, database, API, or frontend changes.
- **Clear "done" condition:** success is objectively testable — the log-based
  assertions that currently fail suite-wide should pass once `caplog` can
  capture structlog output.
- **Good learning value:** it requires understanding how structlog bridges to
  standard-library logging and how pytest captures logs — useful, transferable
  knowledge — while staying small in surface area.
- **Real infrastructure fix, not a fixture tweak:** it repairs test capture for
  the entire suite, which makes for a substantive Week 10 reflection.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/NeamenEmun/pathreview/commit/38394f9d31bd27a4016c0e90ca899b314b413a11

**Reproduction summary:**
Ran `pytest tests/unit/test_batch_processor.py -k empty -v` in my local venv.
`test_empty_chunks_list_returns_empty` fails because `caplog.text` is the empty
string — yet the warning **is** emitted: it shows under pytest's *Captured stdout*
(`[warning  ] Empty chunks list provided to BatchEmbeddingProcessor`), not under
*Captured log*. That proves structlog writes to stdout and never reaches the
stdlib `logging` pipeline that `caplog` hooks into. Tracing it, I found
`core/logging.py::configure_logging()` — the only code that wires structlog into
stdlib logging — is called **only in `scripts/seed_db.py`**, never in the app
under test or the test suite, so during tests structlog runs with its default
stdout logger.

Observed failure:
```
FAILED tests/unit/test_batch_processor.py::...::test_empty_chunks_list_returns_empty
E   AssertionError: assert ('Empty chunks list' in '' or False)
E    +  where '' = <LogCaptureFixture>.text
--- Captured stdout call ---
2026-07-21 20:05:18 [warning  ] Empty chunks list provided to BatchEmbeddingProcessor
1 failed, 10 passed
```

**PLAN.md link:** https://github.com/NeamenEmun/pathreview/blob/fix/159-structlog-pytest-caplog/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
- Fix test-side only (autouse fixture in `tests/conftest.py`) vs. also making
  `configure_logging()` caplog-compatible and calling it at app startup. Leaning
  test-side to keep the change minimal, pending the issue #159 discussion.
- Need to confirm empirically that the import-time bound logger in
  `ingestion/embeddings/batch_processor.py` picks up the test fixture's
  reconfiguration (depends on `cache_logger_on_first_use=False`).

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Working from `PLAN.md`, I completed the core sub-tasks:
- **Sub-task 1 — lock in the reproduction (done Week 8):** confirmed
  `test_empty_chunks_list_returns_empty` fails with an empty `caplog`, while the
  warning shows under *Captured stdout*.
- **Sub-task 2 — add the `autouse` fixture in `tests/conftest.py` (done):**
  `structlog_to_stdlib_logging` reconfigures structlog to end its processor chain
  with `structlog.stdlib.render_to_log_kwargs`, using
  `logger_factory=structlog.stdlib.LoggerFactory()`,
  `wrapper_class=structlog.stdlib.BoundLogger`, and
  `cache_logger_on_first_use=False`, then calls `structlog.reset_defaults()` on
  teardown.
- **Sub-task 3 — level/propagation (done):** confirmed warning/error records are
  captured at the default root level; info-level assertions use
  `caplog.set_level(logging.INFO)` (the idiomatic pytest approach), demonstrated
  in the new tests.
- **Sub-task 5 — decide the config home (done):** chose the test-scoped
  `conftest.py` fixture over modifying `configure_logging()`, so dev/prod log
  rendering is untouched. Also empirically confirmed the Week 8 open question:
  the import-time bound logger in `batch_processor.py` **does** pick up the
  fixture config because `cache_logger_on_first_use=False` makes the lazy proxy
  re-read configuration per call.

**Next steps:**
- Finish sub-task 4 (verify against the full unit suite) and write dedicated
  regression tests in `tests/unit/test_logging_caplog.py`.
- Run `make check` and `make test-unit`, record the pre-existing-failure
  baseline, and confirm my changes add no new failures.
- Open the PR against `ascherj/pathreview`, request peer review, and finalize.

**Blockers:**
None. (The codebase has many pre-existing `make check`/`make test-unit`
failures unrelated to this issue — see Check-in 2 for how I handled the
baseline.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/501

**Branch:** `fix/159-structlog-pytest-caplog`

**What you built:**
An `autouse` pytest fixture (`structlog_to_stdlib_logging` in
`tests/conftest.py`) that reconfigures structlog during the test run to route
events through the standard-library `logging` pipeline via
`structlog.stdlib.render_to_log_kwargs` + `LoggerFactory`, with
`cache_logger_on_first_use=False`. This produces real `LogRecord`s that pytest's
`caplog` can capture, so log-based assertions work suite-wide again, and it
restores structlog defaults on teardown so no state leaks between tests. No
application code changes — dev (`ConsoleRenderer`) and prod (`JSONRenderer`)
output are unaffected.

**Tests added or updated:**
- `tests/conftest.py` — added the `structlog_to_stdlib_logging` autouse fixture.
- `tests/unit/test_logging_caplog.py` (new) — regression tests covering: a
  warning appears in `caplog.text`; the event becomes a `LogRecord` with the
  correct level; info-level capture after `caplog.set_level(INFO)`; error-level
  capture; bound structured fields (e.g. `chunk_count=42`) attach to the record
  without breaking the message; and a logger bound at import time
  (`BatchEmbeddingProcessor`) is captured — the original issue #159 scenario.
- `tests/unit/test_batch_processor.py::test_empty_chunks_list_returns_empty` —
  the pre-existing reproduction test now passes unchanged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> **Pre-existing failures (documented per course guidance).** Before making any
> changes I recorded a baseline on the clean branch: `make test-unit` = **53
> failed / 375 passed**; `ruff check .` = **182 errors**; `black --check .` = 52
> files would reformat; `mypy` (scope `api/ core/ ingestion/ rag/ agent/
> safety/`) = **5 errors** (missing third-party stubs + a numpy/py3.12 stub
> issue). After my changes: unit tests = **52 failed / 382 passed** — my fix
> repairs 1 pre-existing failure (`test_empty_chunks_list_returns_empty`) and
> adds 6 new passing tests, with **zero new failures** (verified by diffing
> JUnit-XML failure sets before/after). `ruff`/`black`/`mypy` counts are
> unchanged, and my two touched files pass `ruff` and `black` cleanly. In this
> codebase with documented pre-existing failures, "passes" means my changes
> introduce no new failures — confirmed.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived. I checked PR
[#501](https://github.com/ascherj/pathreview/pull/501) — no maintainer or peer
comments, no requested changes, no approval. Reviewer response is not an enabled
feature for the Summer 2026 cohort, so this is expected rather than a sign the PR
was overlooked.

**How you responded:**
No changes were required since no feedback came in. The PR remains open and ready
for review with `make check`/`make test-unit` documented as introducing no new
failures. If a reviewer had asked me to move the fix out of `conftest.py` and
into `core/logging.py` (the alternative I flagged in my PR "Notes for Reviewers"),
I would have made `configure_logging()` caplog-friendly with a `ProcessorFormatter`
and called it at app startup, then re-run the baseline diff to prove no
regressions.

---

### Reflection

**What was harder than you expected?**
The actual code change was tiny — a single `conftest.py` fixture — but *proving*
it was safe was the hard part. This repo ships with 53 failing unit tests, 182
ruff errors, and 5 mypy errors before you touch anything, so "did my change break
something?" was not a simple green/red question. I had to stash my work, capture a
clean baseline, then diff failure sets before and after. Worse, my first
comparison falsely flagged `test_readme_scorer` and `test_bias_detector` as
regressions — it turned out a nondeterministic "coroutine was never awaited"
`RuntimeWarning` was being printed mid-line into pytest's `FAILED` summary,
corrupting my text diff. I only trusted the result once I switched to comparing
JUnit-XML `<failure>` nodes instead of grepping stdout.

**What did you learn about working in a large codebase?**
The biggest shift was that "make the test pass" is not the same as "make the right
change." My reproduction test (`test_empty_chunks_list_returns_empty`) could have
been forced green a dozen sloppy ways, but the correct fix had to route *all*
structlog output through stdlib logging without altering how logs render in dev or
production — so I deliberately kept `core/logging.py` and every `logger.*` call
site untouched. I also learned to respect state I didn't write: `batch_processor.py`
binds `logger = structlog.get_logger()` at import time, before any fixture runs,
and I couldn't assume it would pick up my config — I had to confirm empirically
that `cache_logger_on_first_use=False` makes structlog's lazy proxy re-read
configuration per call. In my own projects I'd have just trusted it worked.

**How did AI tools help — and where did they fall short?**
AI was strongest at tracing the root cause fast — connecting "caplog is empty" to
"`configure_logging()` is only called in `scripts/seed_db.py`, so structlog falls
back to its stdout `PrintLogger`" saved me a lot of reading, and it produced the
exact `render_to_log_kwargs` + `LoggerFactory` + `BoundLogger` recipe I needed. It
also structured the tedious safety work: setting up the venv, capturing baselines,
and the JUnit-XML diff. Where it fell short was judgment under noisy signals — it
initially reported false regressions from the polluted `FAILED` lines, and it
can't authenticate to GitHub, so I had to open the PR myself. The lesson was that
AI accelerates the mechanics but I still own verifying that its confident-sounding
output is actually true.

**What would you do differently if you started over?**
I'd establish the pre-existing-failure baseline in Week 8 during reproduction,
not in Week 9 mid-implementation — discovering 53 failing tests while trying to
validate my own change made it briefly unclear whether I'd broken the suite. I'd
also decide the scope question (test-only fixture vs. modifying
`configure_logging()`) earlier and write it down as a decision rather than
carrying it as an open "blocker" across two weeks. Finally, I'd have written the
dedicated `test_logging_caplog.py` regression tests first, so my definition of
"fixed" was concrete before I started changing configuration.

**What are you most proud of?**
Not the fix itself — it's four lines of config — but the rigor I put behind
claiming it was safe. In a codebase this broken it would have been easy to check
the "make test-unit passes" box loosely, but I actually measured 53→52 failures
with 6 new passing tests and *zero* new failures, verified with a method immune to
the stdout noise, and documented the exact before/after numbers in my PR and
journal. Turning "I think it's fine" into "here is the evidence it's fine" is the
part I'd be comfortable defending to a real maintainer.


