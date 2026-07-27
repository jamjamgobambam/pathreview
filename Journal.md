## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/159]

**Issue title:** [structlog output is not captured by pytest caplog — log assertions fail suite-wide]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

tests fail since structlog doesnt propagate into the stblib logging system when testing. any test that uses caplog fails. we have to mod conftest.py or structlog so when testing using caplog will work as intended

**Branch name:** [test/159-configure-structlog-caplog]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[x]I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
Is the scope realistic for Weeks 8–9?

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[x]I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
Are there any blockers or dependencies?

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[x]This issue has no open blockers or dependencies on other unresolved issues.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [commit on branch `test/159-configure-structlog-caplog` — add link after pushing]

**Reproduction summary:**
Ran `pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`. The test failed on `assert "Empty chunks list" in caplog.text` because `caplog.text` was empty — yet the warning `Empty chunks list provided to BatchEmbeddingProcessor` appeared in captured stdout. This confirms structlog emits the event but never routes it through stdlib `logging`, so `caplog` can't see it.

**PLAN.md link:** [https://github.com/oherna25/pathreview/blob/test/159-configure-structlog-caplog/PLAN.md](https://github.com/oherna25/pathreview/blob/test/159-configure-structlog-caplog/PLAN.md)

**Walkthrough video (recommended):** [add Loom link, ≤2 min]

**Blockers or open questions:**
No hard blockers. Open questions carried into Week 9: (1) whether to reuse `configure_logging()` from `core/logging.py` in tests vs. a dedicated test-only structlog config, and (2) confirming structlog's `cache_logger_on_first_use` / module-level `get_logger()` caching doesn't cause the fix to be ignored for already-imported modules.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `tests/conftest.py`: an `autouse` fixture (`configure_structlog_for_caplog`) that reconfigures structlog with a `structlog.stdlib.LoggerFactory` and a processor chain ending in `structlog.stdlib.render_to_log_kwargs`, so structlog events become real stdlib `LogRecord`s that `caplog` can capture. Set `cache_logger_on_first_use=False` so module-level loggers bound at import time (e.g. `batch_processor.py`) pick up the test config, and `structlog.reset_defaults()` on teardown to avoid config leaking across tests. This resolves the two open questions from Week 8: I went with a dedicated test-only config (not reusing `configure_logging()`) to keep `render_to_log_kwargs`/caching concerns isolated to tests, and confirmed the caching concern is handled by `cache_logger_on_first_use=False`. Sub-tasks 1–4 from PLAN.md are done.

**Next steps:**
Open the PR against upstream `main`, request draft feedback, and record a short walkthrough video.

**Blockers:**
None for this issue. Note: the repo's full unit suite has ~52 pre-existing failures in unrelated modules (`test_review_service`, `test_security`, `test_skill_extractor`, `test_tech_detector`, `test_structural_chunker`), and `make check` (lint) reports pre-existing errors across the codebase — neither is caused by or in scope for #159.

---

### Check-in 2 (end of week)

**PR link:** [open PR against `ascherj/pathreview` and add link]
https://github.com/ascherj/pathreview/pull/284

**Branch:** `test/159-configure-structlog-caplog`

**What you built:**
An `autouse` pytest fixture in `tests/conftest.py` that configures structlog to route log events through the stdlib `logging` system during tests. Because the app's `configure_logging()` is never called in tests, structlog otherwise defaults to a `PrintLogger` that writes straight to stdout and bypasses `caplog`; the fixture emits real `LogRecord`s so `caplog`-based assertions work suite-wide.

**Tests added or updated:**
No test assertions were changed. Touched `tests/conftest.py` (the fix). Verified against the existing `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`, which failed before (empty `caplog.text`) and passes after; all 11 tests in that file pass.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
(Note: `make check` and `make test-unit` both fail on pre-existing errors unrelated to #159. The changed file `tests/conftest.py` is lint-clean (`ruff check tests/conftest.py` passes) and the caplog test it enables passes.)

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none
