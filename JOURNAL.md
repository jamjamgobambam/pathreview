# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The app does its logging through `structlog`, but the test suite checks log output
using pytest's built-in `caplog` fixture. Those two don't talk to each other by
default: `structlog.get_logger()` doesn't route its events into Python's standard
`logging` system, so `caplog.text` and `caplog.records` come up empty even when the
code clearly emits the log (the message is visibly printed to stderr). Because of
this, any test that asserts on a log — like `test_empty_chunks_list_returns_empty`
in `tests/unit/test_batch_processor.py` — fails even though the behavior under test
is correct. A successful fix configures `structlog` inside `tests/conftest.py` so its
output propagates into the stdlib logging that `caplog` reads, making the log-based
assertions pass without changing the application code.

**Affected area:** `tests/conftest.py` (test setup), verified against
`tests/unit/test_batch_processor.py`. The application logging in
`ingestion/embeddings/batch_processor.py` is already correct.

**Branch name:** `fix/159-structlog-caplog-capture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope reasoning

- **Tier:** Tier 1, labeled `bug` + `tests`. Scoped to a single config file
  (`tests/conftest.py`), which matches a good first contribution.
- **Do I understand the problem?** Yes. I reproduced the mismatch: the code logs via
  `structlog`, the test reads via `caplog` (stdlib logging), and the two aren't bridged.
- **Is the blast radius small?** Yes. The fix lives in test configuration only — no
  application code changes — so the risk of breaking runtime behavior is low.
- **Can I verify it?** Yes. There's a concrete failing test to run before and after
  (`tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`),
  plus the broader suite to confirm nothing else regresses.
- **Note:** Two other students (`amanadhav`, `oherna25`) also claimed #159. Claims
  aren't exclusive per the module rules, so I'm proceeding with my own approach.
