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
