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

**Reproduction commit link:** [`669ba55` — docs: reproduce #159 — structlog bypasses stdlib logging](https://github.com/ShawarmaOnGit/pathreview/commit/669ba5577b602043a8ce1125a7fb11b2ee6793fb)

**Reproduction summary:**
I ran the single failing test in a clean local environment and confirmed the failure is
real: `caplog.text` comes back as the empty string, while pytest's own stdout capture
shows the warning was definitely emitted. So the log fires, but `caplog` never sees it —
the two logging systems aren't connected.

**PLAN.md link:** [PLAN.md](https://github.com/ShawarmaOnGit/pathreview/blob/fix/159-structlog-caplog-capture/PLAN.md)
(added in [`8f96737`](https://github.com/ShawarmaOnGit/pathreview/commit/8f96737ab2ae727fda700654837461183edf2ff1))

**Walkthrough video (recommended):** _Not recorded — optional and not graded._

**Branch URL (portal submission):**
https://github.com/ShawarmaOnGit/pathreview/tree/fix/159-structlog-caplog-capture

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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Most of the PLAN.md sub-tasks are done. I wrote the failing tests first and confirmed they
were red, then added the autouse fixture in `tests/conftest.py` that routes structlog through
stdlib logging (Plan steps 1-3). The target test `test_empty_chunks_list_returns_empty` now
passes, and I ran the full unit suite to confirm no regressions (Plan steps 4-5). I also
settled the open design question from Week 8: I went with a purpose-built test config instead
of reusing the app's `configure_logging()`, because that function calls `basicConfig` and
fights pytest's own log capture.

**Next steps:**
Add type annotations the pre-commit mypy hook wants on the new test file, commit, push, and
open the PR. Then write Check-in 2 and submit the branch URL through the portal.

**Blockers:**
None. One minor snag: `make typecheck` skips `tests/`, so it did not catch that my test
methods needed return annotations, but the pre-commit hook did. Fixed in a couple minutes.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/917

**Branch:** `fix/159-structlog-caplog-capture`

**What you built:**
An autouse pytest fixture in `tests/conftest.py` that reconfigures structlog to emit through
Python's standard `logging` module during tests, so pytest's `caplog` fixture can actually
capture log events. It resets structlog to its defaults after each test so the global config
does not leak. No application code changed.

**Tests added or updated:**
Added `tests/unit/test_logging_capture.py` with 5 tests. They cover that a structlog warning
becomes one captured record with level `WARNING`, that the record's name matches the logger,
that bound key/value data renders into the captured text, that INFO logs are dropped until a
test opts in with `caplog.at_level(INFO)`, and that a test which logs nothing sees zero
records (the fixture adds no noise). The existing `test_empty_chunks_list_returns_empty` in
`tests/unit/test_batch_processor.py` also flips from failing to passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(This fork has documented pre-existing failures, so "passes" means my changes add no new ones.
Baselines recorded in my PR description: unit tests went 53 failed / 375 passed to 52 failed /
381 passed, exactly one pre-existing failure flipped, and lint/format/typecheck counts are
unchanged.)

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review arrived

**How you responded:**
No changes were required, so the branch stands as submitted in Week 9.

---

### Reflection

**What was harder than you expected?**
Picking the issue. I wanted something small enough that I could actually finish it, but two
other students had already claimed #159 before me, so I had to decide whether to go ahead
anyway. The part I really didn't see coming was the baseline. This fork ships with around 130
intentional bugs, so 53 unit tests were already failing before I touched anything. That meant a
green test suite was never going to be my finish line. I had to define success as 53 failures
going down to 52, and then prove that the one that flipped was mine.

**What did you learn about working in a large codebase?**
The biggest thing is that the fix already existed. `core/logging.py:43` already sets up the exact
structlog to stdlib bridge I needed. Nothing in the test suite ever calls it though. The only
caller in the whole repo is a database seed script. In my own projects, when something doesn't
work it's usually because I haven't written it yet. Here it was code that was written correctly
and just never got reached, which is a very different thing to go looking for. I also had to get
used to working in a suite that's red on purpose, and check failing tests by name instead of
trusting the counts.

**How did AI tools help and where did they fall short?**
Claude Code was most useful for speed of understanding. It explained how structlog's processor
chain and logger factory fit together in plain language, which would have taken me a lot longer
to piece together from the docs. Where it fell short was anything specific to this repo. The
standard structlog setup you find everywhere includes `filter_by_level`, and if I had just pasted
that in, INFO logs would still have been dropped and `caplog` would still have come back empty.
Same bug, new cause. I had to work that out myself and leave it out on purpose. It was the same
with the root cause. I only really believed it after running
`python -c "import structlog; print(structlog.get_config()['logger_factory'])"` and seeing
`PrintLoggerFactory` with my own eyes.

**What would you do differently if you started over?**
Read the code before writing my problem summary. In Week 7 I repeated the issue title's claim
that log assertions fail suite wide, and I wrote that the output goes to stderr. When I actually
checked in Week 8, it turned out exactly one test in the entire repo uses `caplog`, and the
output goes to stdout. Both of those were about twenty minutes of reading away and I wrote them
down as facts instead. I'd also record the regression baseline in the first week instead of the
second, because every claim I made later depended on it.

**What are you most proud of from this module?**
Not the PR itself. It's the before and after table in my PR description, where I compared the
failing test names before and after my change instead of just the counts, so a reviewer can
confirm that nothing quietly swapped places. A close second is writing down why I didn't reuse
the app's own `configure_logging()`. It calls `basicConfig`, caches loggers, and reads the log
level from settings, so a maintainer can disagree with that decision instead of guessing at my
reasoning. And I'm glad I put my two Week 7 mistakes in the journal instead of quietly editing
them out.
