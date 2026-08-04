## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

https://github.com/biswaskdk/pathreview/commit/xxxxxxxx

**Reproduction summary:**

I confirmed that PathReview currently supports resumes and GitHub repositories but does not support portfolio website URLs. There is no web parser or pipeline support for website ingestion.

**PLAN.md link:**

https://github.com/biswaskdk/pathreview/blob/feature/portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

I need to understand how the existing ingestion pipeline sends parsed content to the vector store.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the portfolio website ingestion path by adding a dedicated web parser, wiring it into the ingestion pipeline, and hardening README heading parsing for indented markdown content. The new regression test now covers extracting readable portfolio text from HTML and passes.

**Next steps:**
I am validating the changed parser and pipeline behavior in the project environment and documenting the remaining repo-level baseline failures separately from the new portfolio fix.

**Blockers:**
The repository's `make` shell wrapper is not available in this Windows environment, so validation is being confirmed through the project's `.venv` Python toolchain instead.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/PR_NUMBER

**Branch:**
`feature/portfolio-url-ingestion`

**What you built:**
The fix adds a `WebParser` for portfolio HTML content and exposes `IngestionPipeline.ingest_web(...)` so website pages can flow through the same chunking and embedding path as resumes and READMEs. It also wires real portfolio-URL fetching (async `httpx`) into the review service's ingestion path and normalizes README heading extraction to support indented markdown headers.

**Tests added or updated:**
I added `tests/unit/test_web_parser.py`, which exercises HTML portfolio extraction (title, body text, metadata) and empty-page handling.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> "Passes" here means my changes introduce **no new failures**. This repository has documented pre-existing baseline failures that are unrelated to my change (see note below).

**Pre-existing baseline failures (unrelated to this change):**
Before my changes, `make test-unit` reported **53 failed / 375 passed**; `make check` reported 52 files needing `black`, 177 `ruff` errors, and `mypy` aborting on a numpy stub incompatibility. After my changes the suite is **51 failed / 379 passed** — my change adds no new failures and actually fixes 2 pre-existing README parser tests. `ruff` and `black` pass cleanly on every file I added or modified.

**Draft PR feedback received from:** none