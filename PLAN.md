## Solution plan

**Issue:** [#159 — structlog output is not captured by pytest `caplog`; log assertions fail suite-wide](https://github.com/ascherj/pathreview/issues/159)

### Understand

**Root cause.** The application logs through **structlog**, but nothing configures
structlog to route events into Python's standard library `logging` during tests. pytest's
`caplog` fixture only captures records that pass through stdlib `logging`, so caplog-based
assertions see nothing.

Chain of causes, verified in the code and at runtime:

- `core/logging.py` defines `configure_logging()`, which *is* caplog-friendly — it calls
  `structlog.configure(..., logger_factory=structlog.stdlib.LoggerFactory())` and
  `logging.basicConfig(...)`. But this function is **never invoked in the test path**: its
  only caller is `scripts/seed_db.py`, and it is not called from `api/main.py` either.
- `ingestion/embeddings/batch_processor.py` binds its logger at **import time** with bare
  structlog: `logger = structlog.get_logger()`.
- With nothing configured, structlog falls back to its **default** setup, which uses
  `PrintLoggerFactory`. That prints rendered lines to `sys.stdout` and **bypasses stdlib
  `logging` entirely**, so no `LogRecord`s are ever created.
- `tests/conftest.py` has **no logging setup** — only two string fixtures.

**Expected vs. actual.**
- *Expected:* a log event emitted by code under test appears in `caplog.records` /
  `caplog.text`, so assertions like `assert "Empty chunks list" in caplog.text` pass.
- *Actual:* `caplog.text == ''` and `caplog.records == []` while the message is printed to
  stdout — the assertion fails even though the code logged correctly.

**Reproduction (confirmed locally):**
```
pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q
```
```
E   AssertionError: assert ('Empty chunks list' in '' or False)
---------------------------- Captured stdout call ----------------------------
2026-... [warning  ] Empty chunks list provided to BatchEmbeddingProcessor
```

### Map

Files and symbols involved:

- **`tests/conftest.py`** — *primary file to change.* Add structlog configuration (and/or a
  session-scoped autouse fixture) that routes structlog through stdlib `logging` so `caplog`
  captures records.
- **`core/logging.py`** — reference for the production config (`configure_logging()`,
  `structlog.stdlib.LoggerFactory`, processor list). Decide whether to reuse it or mirror a
  minimal test-only variant. Likely read-only.
- **`ingestion/embeddings/batch_processor.py`** — where the bare `structlog.get_logger()` is
  bound at import time; the concrete symptom lives here. Read-only.
- **`tests/unit/test_batch_processor.py`** — the failing test (`test_empty_chunks_list_returns_empty`)
  used as the reproduction and first verification target. May not need changes.
- **`pyproject.toml`** — `[tool.pytest.ini_options]` (no logging config today); check whether
  a `log_cli`/level setting is needed. Likely read-only.

### Plan

1. **Add a test-scoped structlog configuration in `tests/conftest.py`** using
   `logger_factory=structlog.stdlib.LoggerFactory()` and stdlib-friendly processors
   (`structlog.stdlib.add_log_level`, `filter_by_level`, and a renderer compatible with
   `ProcessorFormatter`) so structlog events become stdlib `LogRecord`s.
2. **Apply the config before any import-time logger binds.** Set it at conftest import time
   or via a session-scoped `autouse=True` fixture, and use `cache_logger_on_first_use=False`
   so a stale default-cached logger can't win.
3. **Verify the reproduction now passes:** re-run the single repro test, then run the whole
   unit suite (`pytest tests/unit -q`) to confirm the fix is suite-wide and introduces no
   regressions.
4. **Handle log level for caplog:** ensure the stdlib level lets the asserted levels through
   (e.g. `caplog.set_level(logging.INFO)` where needed, or set a sensible default level in
   the fixture) since some code paths log at INFO.
5. **Keep production logging untouched** and run the project checks (ruff/black/mypy per
   `make check` and `make test-unit`) before opening the PR.

### Inputs & outputs

- **Input:** log events emitted via structlog (`logger.warning(...)`, `logger.info(...)`,
  etc.) by code under test during a pytest run.
- **Output / change:** those events are emitted through stdlib `logging` as `LogRecord`s, so
  `caplog.records` and `caplog.text` are populated and assertions pass. The change is
  confined to test configuration; **production logging behavior (`core/logging.py`) is
  unchanged**, and no application source is modified.

### Risks & unknowns

- **Import-time logger caching.** `batch_processor.py` binds `logger` at import and
  `core/logging.py` uses `cache_logger_on_first_use=True`. If a module logs during import
  before the test config applies, a default logger could be cached. Mitigation: configure at
  conftest import time and set `cache_logger_on_first_use=False` in tests.
- **caplog capture level.** caplog's handler defaults to WARNING; INFO/DEBUG assertions may
  need `caplog.set_level(...)`. Unknown until the broader suite is run — need to inventory
  which tests assert on which levels (grep `caplog` across `tests/`).
- **Renderer/formatter mismatch.** Pairing `structlog.stdlib.LoggerFactory()` with the wrong
  final processor can raise or mangle output; may need
  `structlog.stdlib.ProcessorFormatter.wrap_for_formatter`. Validate against `core/logging.py`.
- **Process-wide global config.** `structlog.configure()` is global; a test-only config could
  affect tests that (implicitly) expect the default. Low risk given no such tests today, but
  worth a full-suite run.
- **No existing pytest logging config** in `pyproject.toml` to build on, so behavior is
  established from scratch.

### Edge cases

- **No log emitted:** `caplog` legitimately empty; assertions that expect nothing still hold.
- **Multiple levels** (debug/info/warning/error) all captured when the level is set
  appropriately — not just WARNING.
- **Loggers bound at import time** (the `batch_processor.py` case) must still be captured.
- **Structured kwargs** in events (e.g. `logger.info("...", chunk_count=250)`): the human
  message must remain assertable via both `caplog.text` and `record.message`.
- **`record.levelname` / `record.message` assertions:** `add_log_level` must map structlog
  levels to stdlib levels correctly.
- **Repeated configuration** across many test modules must be idempotent (no duplicate
  handlers, no duplicated output).

---

## Appendix — Infrastructure note (separate from #159, left unfixed)

While bringing the stack up per `docs/SETUP.md`, the `vector-db` container
(`chromadb/chroma:0.4.22`) crashed on startup and exited (1):

```
AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.
```

Root cause (from the container's own startup logs): the image ships numpy 1.26.3, but its
boot-time step "Rebuilding hnsw to ensure architecture compatibility" runs an **unpinned**
`pip install chroma-hnswlib numpy`, which upgrades numpy to 2.2.6 inside the container.
chroma 0.4.22's `api/types.py` then uses `np.float_` (removed in numpy 2.0) and import
fails. Pinning numpy in `pyproject.toml` would **not** help, since the container reinstalls
numpy from PyPI at startup. The likely real fix is bumping the chroma server image (and the
matching `chromadb` client pin) to a 0.5.x line that no longer uses the removed API.

This is unrelated to #159 and **left unfixed**: #159 needs only unit tests, which run fully
against mocks (`tests/unit/test_batch_processor.py` uses `Mock()` for the embedding provider
and vector db; `tests/conftest.py` has no service-dependent fixtures), so no live vector-db
is required to reproduce or fix it.
