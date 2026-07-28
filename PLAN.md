# PathReview solution plan

## Solution plan

**Issue:** [#159 — structlog output is not captured by pytest caplog — log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand

**Expected:** a test that logs via `structlog.get_logger()` and asserts on
`caplog.text` / `caplog.records` should see that log record, the same way it
would if the code under test used stdlib `logging` directly.

**Actual:** `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`
fails with `caplog.text == ''`, even though the warning is visibly logged
(it shows up under pytest's "Captured stdout call" section).

**Root cause:** `core/logging.py::configure_logging()` is the one place in this
codebase that wires structlog to stdlib logging — it calls
`structlog.configure(..., logger_factory=structlog.stdlib.LoggerFactory())`,
which is what makes `structlog.get_logger()` calls flow into a real
`logging.Logger` (and therefore into any handler attached to the root logger,
including pytest's `caplog` handler). But `configure_logging()` is only ever
called from `scripts/seed_db.py` — never from `tests/conftest.py`, and never
from the app's own startup path (`api/main.py`). Without it, structlog falls
back to its own default global configuration, which renders and writes events
directly to stdout through its own processor chain, completely bypassing the
stdlib root logger. `caplog` has nothing to attach to, so it captures nothing.

This is a suite-wide gap, not a one-test issue: `structlog.get_logger()` is
used in 37 places across `api/`, `agent/`, `rag/`, `ingestion/`, and `safety/`.
Only one test currently asserts on `caplog` for structlog output, but any test
written against that pattern in the future would hit the same failure.

### Map

- `tests/conftest.py` — needs a new fixture that configures structlog for the
  test process so log calls route through stdlib logging before any test runs.
  This is the only file expected to change to fix the issue itself.
- `core/logging.py` — not modified, but `configure_logging()`'s processor
  chain and use of `structlog.stdlib.LoggerFactory()` is the reference pattern
  the new test fixture should mirror (adapted for test-time needs, e.g. no
  JSON/pretty renderer split, no dependency on `core.config.settings.app_env`).
- `tests/unit/test_batch_processor.py` — not modified; its existing
  `test_empty_chunks_list_returns_empty` test is the verification signal —
  it should pass once the fixture is in place, with no change to the test
  itself.

### Plan

1. Add an autouse fixture in `tests/conftest.py` (e.g. `configure_structlog_for_tests`)
   that calls `structlog.configure(...)` with
   `logger_factory=structlog.stdlib.LoggerFactory()` and a processor chain
   ending in a renderer that produces a plain string, so each
   `structlog.get_logger()` call ends up as a normal `logging.Logger` call
   that pytest's `caplog` handler (attached to the root logger) can see.
2. Decide fixture scope: session-scoped `autouse=True` (configure once) vs.
   function-scoped (safer against state leaking between tests, but reruns
   `structlog.configure` per test). Prefer function-scoped unless it proves too
   slow, since `structlog.configure` is process-global and could bleed
   directional state between tests otherwise.
3. Run `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`
   and confirm `caplog.text` now contains `"Empty chunks list"`.
4. Run the full test suite (`.venv/Scripts/python.exe -m pytest -q`) to confirm
   no regressions — in particular, that nothing relies on structlog's default
   stdout rendering during tests (checked: no test currently uses
   `capsys`/`capfd` to assert on log output, so this is low risk today).
5. Add a short comment in `tests/conftest.py` explaining why the fixture
   exists (replacing/updating the current reproduction-note docstring), so
   future contributors understand the bridge is intentional infrastructure,
   not incidental.

### Inputs & outputs

**Input:** any `structlog.get_logger()` call made by application code during
a test run (event name + bound key/value context).

**Output:** the same log event delivered to the stdlib root logger, so
`caplog.text` and `caplog.records` observe it — without changing what gets
printed to stdout during normal (non-test) runs of the app, and without
requiring individual tests to opt in (it should work for any test that uses
`caplog`, not just ones written with structlog in mind).

### Risks & unknowns

- **Global state collision:** `structlog.configure()` sets process-global
  state. If a test or fixture elsewhere calls `configure_logging()` directly
  (currently only `scripts/seed_db.py` does, so low risk today) it could
  clobber the test fixture's configuration or vice versa — need to grep for
  any future direct calls before merging.
- **`cache_logger_on_first_use`:** the real `configure_logging()` sets this to
  `True`. If the test fixture does the same and a module-level
  `logger = structlog.get_logger()` is imported before the fixture runs (e.g.
  at collection time via `import ingestion.embeddings.batch_processor`), the
  logger could cache a pre-fixture configuration. Need to verify this doesn't
  happen with pytest's normal import/fixture ordering.
- **Renderer choice affects `caplog.text` readability:** using
  `structlog.stdlib.ProcessorFormatter.wrap_for_formatter` requires a
  `ProcessorFormatter`-based handler to fully render output; without one,
  `record.getMessage()` may not look like a normal rendered string. Simpler
  alternative: render to a plain string in the fixture's processor chain
  (e.g. `structlog.processors.KeyValueRenderer()` or similar) before handing
  off to `LoggerFactory()`, so the stdlib logger just receives a string.
  Needs a quick prototype to confirm which approach caplog picks up cleanly.
- **Test isolation across pytest-xdist (if ever adopted):** global
  `structlog.configure` state is per-process, so parallel test workers would
  each need their own configuration — not an issue today (no xdist in use),
  but worth a comment if it's added later.

### Edge cases

- Tests that call `caplog.set_level(logging.DEBUG)` (or another explicit
  level) should still work — the fixture must not hardcode a level that
  overrides what individual tests set.
- Tests that don't use `caplog` at all should see no behavior change (no new
  stdout noise, no performance regression from reconfiguring structlog on
  every test if function-scoped).
- Log calls made with structured kwargs (e.g. `logger.info("...", count=5)`)
  should still surface the event text in `caplog.text` even if the extra
  key/value context is rendered differently than in production JSON logs.
- Exceptions logged via `logger.error(..., exc_info=True)` or similar should
  still be capturable by `caplog.records[i].exc_info`, since some tests may
  eventually assert on that.
