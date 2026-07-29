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

**Cohort ledger:** [x] Issue added to cohort ledger

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

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _(this commit — permalink added in the follow-up entry below)_

**Reproduction summary:**
I ran the single failing test in a clean local environment and confirmed the failure is
real: `caplog.text` comes back as the empty string, while pytest's own stdout capture
shows the warning was definitely emitted. So the log fires, but `caplog` never sees it —
the two logging systems aren't connected.

**PLAN.md link:** _(added in Week 8 planning commit)_

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
None blocking. One open design question I'll settle in Week 9: whether to reuse the
app's existing `configure_logging()` from `core/logging.py` or write a purpose-built
test configuration in `conftest.py`. I'm currently leaning toward the latter — see
PLAN.md for the reasoning.

---

### Reproduction steps

Reproduced on `structlog 26.1.0` / `pytest 9.1.1`.

```bash
python -m pytest "tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty" -v
```

**Observed output:**

```
FAILED tests/unit/test_batch_processor.py::...::test_empty_chunks_list_returns_empty

>       assert "Empty chunks list" in caplog.text or any(
            "empty" in record.message.lower() for record in caplog.records
        )
E       AssertionError: assert ('Empty chunks list' in '' or False)
E        +  where '' = <_pytest.logging.LogCaptureFixture object at 0x107927e00>.text
E        +  and   False = any(<generator object ...>)

tests/unit/test_batch_processor.py:42: AssertionError
----------------------------- Captured stdout call -----------------------------
2026-07-29 02:07:26 [warning  ] Empty chunks list provided to BatchEmbeddingProcessor
=========================== short test summary info ============================
1 failed in 1.91s
```

The two highlighted lines are the whole issue side by side: `caplog.text` is `''`, yet
the warning text appears under **Captured stdout**. The application code at
`ingestion/embeddings/batch_processor.py:40` is doing its job correctly.

### Root cause (confirmed, not inferred)

I checked structlog's active configuration directly rather than assuming:

```bash
python -c "import structlog; print(structlog.get_config()['logger_factory'])"
# <structlog._output.PrintLoggerFactory object at 0x101a59010>
```

Because nothing configures structlog during the test run, it falls back to its default
`PrintLoggerFactory`, which writes **straight to stdout** and never touches Python's
standard `logging` module. `caplog` is implemented as a stdlib logging handler, so a
record that never enters stdlib logging can never reach it. That is why the message is
visible in captured stdout but absent from `caplog.text`.

The correct bridge already exists in this repo — `core/logging.py:43` sets
`logger_factory=structlog.stdlib.LoggerFactory()`, which *does* route events into stdlib
logging. It simply is never invoked from the test suite: the only caller of
`configure_logging()` is `scripts/seed_db.py:20`.

### Scope correction to my Week 7 entry

Two details from Week 7 I got wrong and want on the record:

1. The issue title says log assertions fail **suite-wide**. In practice, exactly **one**
   test in the entire suite currently uses `caplog` (`tests/unit/test_batch_processor.py:36`).
   The fix is still worth making — it unblocks every future log assertion — but the
   present blast radius is one test, not many.
2. I wrote that the message prints to **stderr**. It is actually **stdout**; structlog's
   default `PrintLoggerFactory` writes to stdout.

### Regression baseline

Recorded before changing anything, so I can prove Week 9 introduces no new failures:

```
python -m pytest tests/unit -q      →  53 failed, 375 passed
python -m pytest tests/unit/test_batch_processor.py -q  →  1 failed, 10 passed
```

The 53 failures are pre-existing and unrelated to #159 (this fork is seeded with ~130
intentional issues). Of the 11 tests in `test_batch_processor.py`, the single failure is
the `caplog` one. My success criterion is therefore **52 failed / 376 passed**, not a
green suite.
