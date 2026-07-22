## Solution plan

**Issue:** structlog output is not captured by pytest caplog — log assertions fail suite-wide
— https://github.com/ascherj/pathreview/issues/159

### Understand

**Expected:** When code under test logs via structlog (e.g.
`logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")`),
pytest's `caplog` fixture should capture that record so a test can assert on
`caplog.text` / `caplog.records`.

**Actual:** `caplog` captures nothing. The reproducing test
`tests/unit/test_batch_processor.py::test_empty_chunks_list_returns_empty`
fails with `assert ('Empty chunks list' in '' ...)` — `caplog.text` is the empty
string — even though the log line *is* emitted (it appears under pytest's
"Captured stdout", not "Captured log").

**Root cause (verified):** `core/logging.py::configure_logging()` is the only
place structlog is wired into the standard-library `logging` module (via
`structlog.stdlib.LoggerFactory`). But a repo-wide search shows it is called
**only in `scripts/seed_db.py`** — never by the app under test and never by the
test suite. With structlog left unconfigured during tests, it falls back to its
**default configuration**, whose logger factory prints rendered events straight
to `sys.stdout` and never routes them through stdlib `logging`. Because
`caplog` only observes records that pass through stdlib `logging`, it sees
nothing — hence "log assertions fail suite-wide."

**Secondary factor:** even when `configure_logging()` *is* called, its processor
chain ends in `ConsoleRenderer`/`JSONRenderer` (which flatten the event to a
string before stdlib sees it) and it sets `cache_logger_on_first_use=True`.
Neither is friendly to `caplog`, which wants real `LogRecord`s and picks up its
handler per-test. So the durable fix must make structlog hand structured records
to stdlib during tests, not just call the existing function.

### Map

Files/functions expected to be involved:
- `core/logging.py` — `configure_logging()` (the structlog config) and
  `get_logger()`. Primary place the routing behavior is decided.
- `tests/conftest.py` — shared fixtures; currently has **no** logging fixture.
  Best home for an `autouse` fixture that configures structlog for capture.
- `tests/unit/test_batch_processor.py` — the failing test; the reproduction
  target and first verification point (should go green with no change to the
  test itself).
- `core/config.py` — `log_level` (default `INFO`) and `app_env` (default
  `development`); relevant because level filtering can still drop records.
- `scripts/seed_db.py` — current sole caller of `configure_logging()`; check the
  fix doesn't change its behavior.

### Plan

1. **Lock in the reproduction** (done): run
   `pytest tests/unit/test_batch_processor.py -k empty -v` and confirm it fails
   with an empty `caplog`, while the message shows under Captured stdout.
2. **Add an `autouse` fixture in `tests/conftest.py`** that reconfigures
   structlog for tests to route through stdlib logging: use
   `logger_factory=structlog.stdlib.LoggerFactory()`, end the processor chain
   with `structlog.stdlib.render_to_log_kwargs` (hand event + fields to stdlib),
   and set `cache_logger_on_first_use=False` so the per-test handler is honored.
3. **Ensure level/propagation** so records actually reach `caplog`: within the
   fixture (or via `caplog.set_level`) make the relevant logger propagate and
   sit at `INFO`/`DEBUG`, so `info`/`warning`/`error` calls are all captured.
4. **Verify** the target test passes unchanged, then run the full unit suite
   (`make test-unit`) to confirm the other 10 tests in that file — and the rest
   of the suite — still pass and that stdout-based expectations aren't broken.
5. **Decide the config home** (investigation, then implement): keep the fix
   test-scoped in `conftest.py`, or additionally make `configure_logging()`
   caplog-compatible (ProcessorFormatter) and call it at app startup. Prefer the
   smallest change that fixes capture without altering dev/prod log formatting.

### Inputs & outputs

- **Input:** structlog log calls made by code under test — an event string plus
  optional bound key/values (e.g. `logger.info("...", chunk_count=total)`).
- **Output / behavior change:** those calls now produce standard-library
  `logging.LogRecord`s that propagate to pytest's capture handler, so
  `caplog.records` and `caplog.text` are populated and log assertions pass.
- **No public signatures change.** `logger.warning(...)`/`logger.info(...)`
  call sites are untouched. The change is configuration- and fixture-level. If
  `core/logging.py` is touched, the observable difference is that structlog
  emits stdlib-compatible records; dev (`ConsoleRenderer`) and prod
  (`JSONRenderer`) *runtime* output must remain visually unchanged.

### Risks & unknowns

- **Global reconfiguration leaks (tests/conftest.py):** an `autouse` structlog
  fixture reconfigures a process-global. It could alter output for the other 10
  tests in `test_batch_processor.py` or other suites. Mitigation/investigation:
  run `make test-unit` before and after and diff pass/fail.
- **Import-time logger binding (ingestion/embeddings/batch_processor.py:7):**
  `logger = structlog.get_logger()` is bound at import, before the fixture runs.
  With `cache_logger_on_first_use=False`, structlog's lazy proxy should re-read
  config at call time — but this must be confirmed empirically, not assumed.
- **Level filtering (core/config.py `log_level=INFO`):** if the effective stdlib
  level stays at `WARNING`, `info`-level assertions elsewhere would still fail;
  the fixture must set the level explicitly.
- **Unknown — maintainer preference:** fix in `tests/conftest.py` only, vs.
  making `configure_logging()` itself caplog-friendly and invoking it at startup.
  Investigation path: re-read the issue #159 discussion and `docs/CONTRIBUTING.md`.

### Edge cases

1. **A warning-level log** (`logger.warning(...)`, the failing test's case) — must
   be captured.
2. **Info- and error-level logs** (`logger.info(...)`, `logger.error(...)` used
   throughout `batch_processor.py`) — must also be captured, so the fix can't be
   scoped to a single level.
3. **Structured/bound fields** (`logger.info("msg", chunk_count=5)`) — extra
   key/values must not break capture; the record's message should remain
   assertable.
4. **Tests that do not use `caplog`** — the 10 currently-passing tests must keep
   passing; the fixture must not change their behavior or their stdout.
5. **Test isolation** — reconfiguring per test must not leak logging state
   between tests (no cross-test contamination of handlers/levels).
