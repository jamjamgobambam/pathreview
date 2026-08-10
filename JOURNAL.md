# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/159

**Issue title:** structlog output is not captured by pytest caplog — log assertions fail suite-wide

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The backend does its logging through `structlog`, but during test runs structlog
is never wired into Python's standard-library `logging` system. pytest's `caplog`
fixture only sees records that flow through stdlib `logging`, so any test that
asserts on `caplog` comes up empty and fails — even when the code under test
genuinely emits the expected log line (the message shows up in captured stdout,
but `caplog.text` and `caplog.records` stay empty). The canonical failure is
`test_empty_chunks_list_returns_empty` in `tests/unit/test_batch_processor.py`,
but the gap affects caplog-based assertions across the whole suite. The root cause
is that `core/logging.py::configure_logging()` (which would route structlog through
stdlib logging) is never invoked in the test path, so structlog falls back to its
default `PrintLoggerFactory` that prints straight to stdout and bypasses `logging`.
A successful fix configures structlog in `tests/conftest.py` so its events
propagate into stdlib logging, making `caplog` capture them and the existing
assertions pass — without coupling the tests to production/env-dependent rendering.
This affects the test harness (`tests/conftest.py`) and the logging setup in
`core/logging.py` / `ingestion/embeddings/batch_processor.py`.

**Branch name:** test/159-structlog-caplog-propagation

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" — scope reasoning

- **Tier fit:** Tier 1, labeled `good for first-time contributors`. Appropriate for a
  first contribution to a large multi-module codebase.
- **Scope is well-bounded:** The fix is concentrated in test configuration
  (`tests/conftest.py`) plus understanding the existing `core/logging.py` setup. It
  does not require touching application/business logic or the RAG/agent pipelines.
- **Reproducible:** There is a single, deterministic repro command
  (`pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`)
  and a clear pass/fail signal.
- **No external service dependency:** The failing unit test runs entirely against
  mocks (mocked embedding provider and vector db), so a live vector-db / Docker
  stack is not required to reproduce or verify the fix. (Note: the `chromadb/chroma:0.4.22`
  container crashes on startup due to a NumPy 2.0 incompatibility, but that is
  unrelated to #159 and out of scope here.)
- **Clear definition of done:** caplog-based assertions capture structlog events and
  the previously failing test passes, with no regressions elsewhere.
---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/amanadhav/pathreview/commit/247ed55

**Reproduction summary:** Ran the unit test
`tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q`
against mocks (no Docker needed). It failed with `assert ('Empty chunks list' in '' or False)`
— `caplog.text`/`caplog.records` were empty — while the exact warning
("Empty chunks list provided to BatchEmbeddingProcessor") still appeared under pytest's
"Captured stdout call", confirming structlog's default `PrintLoggerFactory` bypasses stdlib
logging so `caplog` never sees the record.

**PLAN.md link:** https://github.com/amanadhav/pathreview/blob/test/159-structlog-caplog-propagation/PLAN.md

**Walkthrough video (recommended):** _(not recorded yet)_

**Blockers or open questions:** Two design questions for the fix (documented in PLAN.md):
whether to reuse `core/logging.py`'s `configure_logging()` or write a dedicated test config
in `conftest.py`, and how to handle `cache_logger_on_first_use` given `batch_processor.py`
binds its logger at import time. Also need to inventory which existing tests assert on which
log levels so caplog's capture level is set correctly.

### Reproduction steps (detailed)

1. `docker compose up -d` (only `db` and `redis` are needed; `vector-db` crashes for an
   unrelated chroma/numpy reason documented in PLAN.md — not required for this issue).
2. Create the venv and install deps: `python -m venv .venv` then
   `.venv/Scripts/pip install -e ".[dev]"`.
3. Run the failing test:
   ```
   pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q
   ```
4. Observe: assertion fails on empty `caplog.text`, while the log line is visible on stdout.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Completed the substantive `PLAN.md` subtasks: added the RED regression test proving the stdout-only failure, added import-time structlog configuration in `tests/conftest.py`, and completed focused canonical verification of both the new routing contract and the unchanged batch-processor warning contract.

**Next steps:** Run broad validation, request peer/mentor review, and complete final PR follow-up.

**Blockers:** None for #159. The repository has unrelated pre-existing unit, lint, formatting, and type-check baselines; these are tracked separately and do not block the focused logging fix.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/596

**Branch:** `test/159-structlog-caplog-propagation`

**What you built:** Added test-only structlog routing through Python's standard-library logging so pytest `caplog` receives emitted records. Configuration runs when `tests/conftest.py` is imported—before test modules bind loggers—and disables first-use caching so import-time lazy loggers resolve the active test configuration without changing production logging.

**Tests added or updated:** Added `tests/unit/test_logging_config.py`, which creates an import-time logger and verifies that one INFO `LogRecord` contains both the event and its structured field. The canonical `tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty` test remains unchanged and still asserts the empty-list warning while returning an empty list.

**Self-review confirmation:**

- [x] make check passes
- [x] make test-unit passes

Per the course's pre-existing-failure rule, GNU Make was unavailable in this Windows shell, so equivalent commands were run instead. The changed files and focused tests pass, and comparison/baseline verification shows no new failures: the focused run reports 12 passed; the full unit run reports 377 passed and 52 pre-existing failures; full Ruff reports 182 pre-existing errors; Black reports 52 pre-existing files needing formatting; and Mypy reports 19 pre-existing errors in 11 files. The changed Python files pass Ruff, Black `--check`, focused Mypy, and diagnostics.

**Draft PR feedback received from:** `none` — the user opened the ready-for-review PR manually after tooling authentication failed.

**Implementation commit:** https://github.com/amanadhav/pathreview/commit/d9b0f1086ed9b78a1276684c73cb2f644ace1db2

**RED/GREEN evidence:** Before the shared conftest configuration, `tests/unit/test_logging_config.py` failed with `assert 0 == 1`: no matching `caplog` record was captured and the event appeared on stdout. After import-time stdlib routing was added, that test passed, the unchanged canonical empty-list warning test passed, and the combined focused verification completed with 12 passed.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:** No review arrived. PR
[ascherj/pathreview#596](https://github.com/ascherj/pathreview/pull/596)
("test: route structlog logs through pytest caplog") is still open against
`ascherj:main` with zero issue comments, zero review comments, and no reviewers
assigned as of the end of Week 10. Checked the PR page and the GitHub API
(`comments: 0`, `review_comments: 0`, `requested_reviewers: []`, `state: open`)
to confirm. Per the Summer 2026 note, reviewer feedback is not part of this
term's workflow, so this is the expected outcome rather than a stalled PR.

**How you responded:** No reviewer changes to make. I used the week to
self-review instead: re-read the diff on
`test/159-structlog-caplog-propagation` (5 files, +650/-0), re-ran the focused
verification (12 passed) to confirm the branch is still green, and confirmed the
head commit `41d16ad` on the PR matches my local branch tip so a reviewer
arriving late would see the finished work. The one gap I found and noted for
myself is that the PR body is still the repo's unfilled template — the
`Closes #159` line and the Changes/Notes sections were never filled in when I
opened the PR manually after the CLI auth failure. If review does come in, my
first action is to rewrite that description before replying to anything else.

---

### Reflection

**What was harder than you expected?**
The hardest part was not the fix — it was proving what the fix actually did. The
final change to `tests/conftest.py` is about twenty lines, but getting there
meant understanding *ordering*: `ingestion/embeddings/batch_processor.py` binds
its logger at module import time via `structlog.get_logger()`, so anything I
configured inside a pytest fixture ran too late to matter. That's why the
`structlog.configure()` call sits at module level in `conftest.py` and why
`cache_logger_on_first_use=False` is not optional — with caching on, the
import-time lazy proxy would freeze structlog's default `PrintLoggerFactory` and
`caplog` would stay empty no matter what the fixture did. I lost real time
believing my fix was wrong when it was actually correct but running in the wrong
order. Separating "the code is wrong" from "the code ran at the wrong moment"
was the actual skill this issue taught me.

**What did you learn about working in a large codebase?**
That a red test does not mean you broke something. The first time I ran the full
unit suite I saw 52 failures and assumed I had caused a disaster; they were
pre-existing, and so were the 182 Ruff errors, 52 Black-unformatted files, and
19 Mypy errors in 11 files. In my own projects a clean baseline is a reasonable
assumption. Here I had to learn to *measure* the baseline first, then prove my
change added nothing to it — which is a completely different verification habit
than "does the suite pass." I also learned to say no to adjacent breakage: the
`chromadb/chroma:0.4.22` container crashes on startup because of a NumPy 2.0
incompatibility, and it was genuinely tempting to fix it since it was blocking
my `docker compose up`. It had nothing to do with #159, so I documented it in
PLAN.md as out of scope and moved on with mocks instead. Scope discipline felt
like giving up in the moment and was clearly the right call in hindsight.

**How did AI tools help — and where did they fall short?**
AI was strongest at orientation and at mechanical breadth. It got me from "the
issue mentions structlog and caplog" to the right two files
(`core/logging.py::configure_logging()` and `tests/conftest.py`) far faster than
grepping would have, and it explained *why* `caplog` can't see structlog output
— that caplog only observes stdlib `logging` handlers — which was the conceptual
key to the whole issue. It was also useful for the grind: running the Windows
equivalents of `make check` / `make test-unit` when GNU Make wasn't available in
my shell, and diffing baseline failure counts against post-change counts.

Where it fell short was the ordering problem above. Early suggestions had me
configuring structlog inside a fixture, which is the textbook answer and is
wrong for this specific repo because of the import-time logger binding in
`batch_processor.py` — that's repo-specific knowledge no general answer had.
It also could not decide for me whether to reuse `configure_logging()` or write
a dedicated test-only config; reusing production config would have coupled the
tests to env-dependent rendering, and I only saw that tradeoff by reading
`core/logging.py` myself. And when I was staring at an empty `caplog.text`, AI
happily proposed plausible next edits rather than telling me to prove the
mechanism first. Writing the RED probe test
(`tests/unit/test_logging_config.py`, which fails with `assert 0 == 1` before
the conftest change) was the thing that actually resolved it, and that instinct
came from the process, not the tool.

**What would you do differently if you started over?**
Three things. First, I'd write the RED probe test on day one instead of during
implementation week — I spent Week 8 reasoning about the mechanism in prose in
PLAN.md when a ten-line failing test would have proven the same thing in five
minutes and given me a pass/fail signal to iterate against. Second, I'd capture
the baseline failure/lint counts immediately after cloning and paste them into
PLAN.md, so I'd never again have the "did I break 52 tests?" panic. Third, I'd
sort out the GitHub CLI auth *before* submission night. Because it failed, I
opened PR #596 manually through the web UI and pasted the template without
filling it in, which means a reviewer's first impression of my work is an empty
"Closes #" and an empty Changes list — a bad framing for a fix whose whole value
is in the reasoning behind it.

**What are you most proud of from this module?**
The RED/GREEN evidence trail. `tests/unit/test_logging_config.py` creates a
logger at import time, asserts that exactly one INFO `LogRecord` reaches
`caplog` containing both the event name and its structured `routing_probe`
field, and it demonstrably failed before the conftest change and passes after.
Alongside it, the canonical
`test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty`
is completely untouched and now passes on its original assertions — which is the
strongest possible argument that I fixed the harness rather than edited the test
to agree with me. Anyone can read that diff and verify the claim without taking
my word for anything. That's a higher bar than I've held my own projects to.
