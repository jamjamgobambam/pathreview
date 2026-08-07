# Solution plan

**Issue:** [#159 — structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

---

## Understand

**What's broken.** The application logs through `structlog`, but the test suite asserts
on log output using pytest's built-in `caplog` fixture. Nothing configures `structlog`
during a test run, so it falls back to its shipped default `logger_factory` —
`PrintLoggerFactory`, which writes rendered events **straight to stdout** and never hands
them to Python's standard `logging` module.

`caplog` is implemented as a stdlib logging handler attached to the root logger. A log
event that never enters stdlib logging can never reach that handler. So the message is
plainly visible in pytest's captured stdout while `caplog.text` stays empty.

I confirmed the active factory rather than assuming it:

```bash
python -c "import structlog; print(structlog.get_config()['logger_factory'])"
# <structlog._output.PrintLoggerFactory object at 0x101a59010>
```

**Expected vs. actual**, using `test_empty_chunks_list_returns_empty`:

| | |
|---|---|
| **Expected** | `logger.warning("Empty chunks list…")` produces a `LogRecord`, so `caplog.text` contains the message and `caplog.records` holds one WARNING record. |
| **Actual** | `caplog.text == ''` and `caplog.records == []`. The message appears only under pytest's *Captured stdout* section. |

**The fix is test-side only.** The application logging call at
`ingestion/embeddings/batch_processor.py:40` is already correct — it emits a WARNING with
a sensible message. Nothing in `ingestion/` needs to change.

Notably, **the correct bridge already exists in this repo.** `core/logging.py:43` sets
`logger_factory=structlog.stdlib.LoggerFactory()`, which *does* route structlog events
into stdlib logging. It is simply never invoked from the test suite — the only caller of
`configure_logging()` anywhere in the codebase is `scripts/seed_db.py:20`. The fix is
therefore about making the test suite establish an equivalent configuration, not about
inventing a new mechanism.

**Scope note.** The issue title says log assertions fail *suite-wide*. In practice exactly
one test currently uses `caplog` (`tests/unit/test_batch_processor.py:36`). The fix is
still worth making — it unblocks every future log assertion in the project — but I want the
real blast radius on record rather than overstating it.

---

## Map

Files I expect to **touch**:

| File | Change |
|---|---|
| `tests/conftest.py` | The entire fix. Add an autouse fixture that configures `structlog` to emit through stdlib logging, and resets it afterward. Currently holds only `sample_resume_text` and `sample_readme_text` fixtures and imports nothing but `pytest`. |

Files I expect to **read or verify against, but not modify**:

| File | Role |
|---|---|
| `tests/unit/test_batch_processor.py:36` | `test_empty_chunks_list_returns_empty` — the one concrete failing test; my pass/fail signal. Asserts on both `caplog.text` (line 42) and `record.message` (line 43). |
| `ingestion/embeddings/batch_processor.py:40` | The `logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")` emit site. Correct as written; do not change. |
| `core/logging.py:40-45` | The app's existing `structlog.configure()` block. My reference for what a correct configuration looks like, and the source of the `cache_logger_on_first_use=True` hazard noted under Risks. |
| `scripts/seed_db.py:20` | The sole caller of `configure_logging()` — evidence that the app never configures structlog during tests. |
| `pyproject.toml:83-90` | `[tool.pytest.ini_options]`. Defines markers but sets **no** `log_cli` or `log_level`, which is why the root logger sits at its WARNING default. |

Modules that log via `structlog` and would also become assertable once this lands (context,
not targets): `ingestion/pipeline.py`, `agent/orchestrator.py`, `agent/error_handling.py`,
`agent/tools/tech_detector.py`, `agent/tools/market_analyzer.py`,
`core/services/profile_service.py`.

---

## Plan

1. **Add an autouse fixture to `tests/conftest.py`** that calls `structlog.configure()`
   with `logger_factory=structlog.stdlib.LoggerFactory()` and
   `wrapper_class=structlog.stdlib.BoundLogger`. This is the actual bridge: it makes
   structlog emit through `logging.getLogger(name)` instead of printing to stdout.

2. **Set `cache_logger_on_first_use=False`** in that configuration, and build a minimal
   processor chain (`add_log_level`, `StackInfoRenderer`, `format_exc_info`, and a
   `ConsoleRenderer(colors=False)`). Deliberately **omit** `structlog.stdlib.filter_by_level`
   — see Edge cases for why it would silently re-break capture.

3. **Restore global state on teardown** by calling `structlog.reset_defaults()` after each
   test, so the fixture cannot leak configuration into unrelated tests. `structlog.configure()`
   mutates process-global state, so this isolation step is not optional.

4. **Verify the target test flips to passing** by running
   `pytest "tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty" -v`,
   and confirm `caplog.records` now holds one record with `levelname == "WARNING"` — not just
   that the string match succeeds.

5. **Check for regressions against the recorded baseline.** Before any change,
   `pytest tests/unit -q` gives **53 failed / 375 passed**, and
   `pytest tests/unit/test_batch_processor.py -q` gives **1 failed / 10 passed**. Success is
   **52 failed / 376 passed** — exactly one test flipping. The other 52 failures are
   pre-existing and belong to unrelated seeded issues in this fork; a green suite is *not*
   the target and claiming one would be wrong.

---

## Inputs & outputs

**Input.** Structured log events emitted by application code through module-level
`structlog.get_logger()` calls — for example
`logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")` at
`ingestion/embeddings/batch_processor.py:40`, including any bound key/value pairs such as
`chunk_count=total_chunks`.

**Output.** Standard-library `logging.LogRecord` objects delivered to pytest's
`LogCaptureHandler`, so that within a test:

- `caplog.text` contains the rendered event text,
- `caplog.records` is non-empty and each record carries a correct `levelname`
  (`"WARNING"` for the target test) and a `name` matching the emitting module
  (`ingestion.embeddings.batch_processor`).

**What changes.** Only test-time configuration. Concretely:

- `tests/conftest.py` gains one autouse fixture and imports of `structlog` (and `logging`).
- No function signature changes anywhere.
- No application code changes — `ingestion/`, `agent/`, `core/`, and `api/` are untouched.
- No runtime behavior change: production logging still flows through
  `core/logging.py::configure_logging()` exactly as it does today.

**What is explicitly out of scope.** Rewriting `core/logging.py`, changing the assertion
style in `test_batch_processor.py`, or fixing any of the other 52 failing tests.

---

## Risks & unknowns

1. **`structlog.configure()` mutates process-global state.** It is not scoped to a test or
   module. If the fixture configures without restoring, ordering-dependent failures could
   appear in tests that run afterward — the classic symptom being a suite that passes
   file-by-file but fails when run whole. *Mitigation:* `structlog.reset_defaults()` on
   fixture teardown, plus a full-suite run (step 5) rather than trusting a single-file run.

2. **Reusing `configure_logging()` from `core/logging.py` looks tempting but is the wrong
   call.** Three concrete reasons, each tied to a line: it sets
   `cache_logger_on_first_use=True` (`core/logging.py:44`), which freezes a bound logger's
   underlying factory on first use and can pin a logger to a stale configuration; it calls
   `logging.basicConfig(stream=sys.stdout)` (`core/logging.py:48-52`), which installs a root
   handler that fights pytest's own capture; and it reads `settings.app_env` and
   `settings.log_level` from `core.config` (`core/logging.py:8, 13, 51`), coupling test
   logging to environment configuration. I'm planning a purpose-built test config instead —
   but this is the main design decision I'd want a reviewer's opinion on, since "reuse the
   app's own function" is the more obvious-looking choice.

3. **The renderer choice leaks into `record.message`.** With `ConsoleRenderer`, the rendered
   string becomes the stdlib message, so `record.message` reads
   `'[warning  ] Empty chunks list provided to BatchEmbeddingProcessor'` — the level is baked
   into the text *and* available as `record.levelname`. Line 43 of the test does
   `record.message.lower()`, so it passes either way, but a future test asserting exact
   message equality would be surprised. *Open question:* whether to use
   `structlog.stdlib.ProcessorFormatter` for a cleaner separation between rendered output and
   the raw event. I judged that more machinery than this fix needs, but it is the more
   idiomatic long-term setup.

4. **Unknown: interaction with tests that configure logging themselves.** I grepped and found
   no test calling `configure_logging()`, `basicConfig()`, or `structlog.configure()`, so
   today there is no conflict. That could change, and an autouse fixture would silently win
   over a test's own setup. *Investigation path:* re-run
   `grep -rn "configure_logging\|basicConfig\|structlog.configure" tests/` before finalizing.

5. **Unknown: integration and non-unit test paths.** My baseline covers `tests/unit` only.
   `tests/integration` requires Docker services per the `integration` marker in
   `pyproject.toml:87` and I have not run it. An autouse fixture in the root `conftest.py`
   applies to *every* test, including those. *Investigation path:* attempt an integration run,
   or scope the fixture more narrowly if it proves disruptive.

---

## Edge cases

1. **INFO-level logs are dropped unless the test opts in.** pytest's root logger sits at
   WARNING by default and `pyproject.toml` sets no `log_level`, so
   `logger.info("Starting batch embedding processing", ...)` at
   `ingestion/embeddings/batch_processor.py:46` produces **no** captured record unless the test
   calls `caplog.set_level(logging.INFO)`. I verified both halves of this behavior directly.
   The fix must not paper over it by force-lowering the global level; that would change what
   every other test sees. It should be documented in the fixture docstring instead.

2. **`structlog.stdlib.filter_by_level` in the processor chain would silently re-break
   capture.** It consults the stdlib logger's effective level *before* the record is emitted,
   so with the root logger at WARNING it discards INFO and DEBUG events even when a test has
   called `caplog.set_level(logging.INFO)` — reproducing the original "log fires but caplog is
   empty" symptom for a different reason. It appears in the app chain at `core/logging.py:16`
   and `core/logging.py:29`; it must be omitted from the test chain.

3. **Structured key/value pairs must survive into the captured text.** Calls like
   `logger.info("Starting batch embedding processing", chunk_count=total_chunks)` bind extra
   context. A test asserting on `chunk_count` needs those rendered into the message rather than
   dropped, so the processor chain must end in a renderer that serializes bound values.

4. **Loggers are created at import time.** Every module does `logger = structlog.get_logger()`
   at module scope (e.g. `ingestion/embeddings/batch_processor.py:7`), which runs during pytest
   *collection* — before any fixture executes. This is safe only because `get_logger()` returns
   a lazy proxy that resolves configuration on first *use*, and because
   `cache_logger_on_first_use=False` keeps it from freezing. If either assumption breaks, the
   fixture would configure too late to matter.

5. **Exception context is carried as a bound value, not as `exc_info`.** Logging inside
   `except` blocks — `agent/error_handling.py:43-44` (`logger.error("retry_exhausted", …,
   error=str(e))`) — passes the exception as a plain `error=` key. I grepped the codebase and
   **no** call site uses `logger.exception()` or `exc_info=`, so `format_exc_info` is currently
   a no-op here. Two consequences: a test asserting on exception detail must look for the
   `error=` value in the rendered text, not `record.exc_info`, which will be `None`; and
   `format_exc_info` should still stay in the chain so that any future `logger.exception()`
   call is captured correctly rather than silently losing its traceback.

6. **An empty log run must stay empty.** A test that triggers no logging should still see
   `caplog.records == []`. The fixture must not inject startup or configuration noise of its
   own, or it would break negative assertions like "this path logs nothing."
