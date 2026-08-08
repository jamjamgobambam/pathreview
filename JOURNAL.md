# Contribution Journal — PathReview

**Contributor:** Shawn Blackman (@sh4wnbk)
**Course:** CodePath AI 201, Module 3

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview re-embeds every submitted document, even when the content hasn't changed, wasting embedding API calls on identical re-submissions. The pieces for skipping already exist — `ingestion/pipeline.py` computes a SHA256 content hash, and the `IngestedSource` model in `core/models/ingested_source.py` has an indexed `content_hash` column — but they're never connected: `_check_skip()` queries a placeholder string instead of the ORM model, and `_record_ingested_source()` only logs without writing a database row. A successful fix records each ingested source with its hash and skips the embedding step when the same content is re-submitted, while changed content still ingests normally.

**Selection notes ("Is this right for me?" checklist):**
- **Tier fit:** Tier 2 — the change spans the ingestion pipeline, the ORM model, and the database session. Five prior AI 201 projects (including a RAG pipeline and a Flask backend with an injected data store) cover the same kind of cross-module work. This exact pattern also replicates content-hash caching built for a geospatial research pipeline, so the design decisions (what to hash, where to store it, how to handle a miss) carry over directly.
- **Codebase readiness:** Both referenced files located and read, including the placeholder `_check_skip()` and `_record_ingested_source()` functions the fix will replace.
- **Tests:** No `tests/unit/test_pipeline.py` exists — the required test will be newly authored, following existing unit test patterns.
- **Scope and time:** Unclaimed at time of claiming, no blockers or dependencies; the 4–6 hour estimate fits the Week 8–9 window.

**Branch name:** `feat/13-content-hash-skip-reembedding`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sh4wnbk/pathreview/commit/5230769

**Reproduction summary:**
Added `tests/unit/test_ingestion_pipeline.py`, which ingests identical README content twice and asserts the second pass is skipped. The test fails: both passes embed, and the captured log shows why, with `_check_skip` logging `Could not check if source already ingested error="Mock object has no attribute 'query'"` on each run. That is an `AttributeError` from calling the synchronous `.query()` API on an `AsyncSession`, swallowed by a bare `except Exception`, so the pipeline proceeds as though no check had happened. `_record_ingested_source` logs `Recording ingested source` on both passes while writing no database row.

**PLAN.md link:** https://github.com/sh4wnbk/pathreview/blob/feat/13-content-hash-skip-reembedding/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
No blockers. Four open items carried into Week 9:

- None of the project's quality gates pass on unmodified `main`. `make test-unit` reports 53 failures across `test_bias_detector.py`, `test_pii_scrubber.py`, `test_resume_parser.py`, `test_review_service.py`, and others; `make check` fails at `ruff check .` with 183 errors; the pre-commit mypy hook fails with 12 type errors in `ingestion/chunking/`, `ingestion/embeddings/`, and `ingestion/pipeline.py`. The Week 8 commits were made with `--no-verify` for that reason, documented in the commit message. Ruff, black, and mypy all pass on the added test file, and the suite moves from 53 failures to 54, the single addition being the reproduction test that turns green once the fix lands.
- `IngestionPipeline` has no callers anywhere in the repository, confirmed by `grep -rn "IngestionPipeline("`. Converting its methods to `async` therefore breaks nothing, but the contract is being chosen rather than matched, and the unit tests are its only consumer.
- Whether `_record_ingested_source` should commit or flush is unsettled. Committing makes the pipeline self-contained; flushing would leave transaction control to a caller that does not yet exist.
- `core/services/review_service.py` constructs `IngestedSource` with a `raw_data=` keyword matching no column on the model. It is a separate ingestion path that never touches `IngestionPipeline`, so it stays out of scope and will be noted for the reviewer in the pull request.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix in `ingestion/pipeline.py`. `_check_skip` now runs a real `select(IngestedSource)` matched on `content_hash`, `profile_id`, and `source_type` and returns a skip result when a row exists; `_record_ingested_source` persists a row and commits. The three `ingest_*` methods and both helpers are now async to match the `AsyncSession` the app supplies, and `_hash_content` returns the full 64-char digest for storage while `source_id` keeps its 16-char slice. Rewrote `tests/unit/test_ingestion_pipeline.py` as six passing async tests driven through an in-memory fake session, covering skip on identical re-ingest, no skip on changed content, per-profile scoping, empty-check, row persistence with commit, and full-digest hashing. That closes sub-tasks 1 through 6 from PLAN.md. Draft PR #305 is open against the upstream repo with the description filled in.

**Next steps:**
Request peer review in the cohort Slack channel, address any feedback, then flip the PR from draft to ready. Add Check-in 2 at submission with the PR link and self-review boxes.

**Blockers:**
None. The pre-existing broken gates (53 test failures, 183 lint errors, 12 mypy errors on `main`) are documented in the PR and unaffected by this change.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/305

**Branch:** `feat/13-content-hash-skip-reembedding`

**What you built:**
Wired content-hash deduplication into the ingestion pipeline for issue #13. `_check_skip` queries the real `IngestedSource` model on `(content_hash, profile_id, source_type)` and returns a skip result when a match exists; `_record_ingested_source` persists a row and commits. The pipeline's database access is async to match the `AsyncSession` the app supplies, so identical content is embedded once and skipped on re-ingest while changed content still ingests. Following peer review, the record function's error path was changed to let database errors surface rather than roll back a shared session.

**Tests added or updated:**
`tests/unit/test_ingestion_pipeline.py`, rewritten as seven async tests driven through a stateful in-memory session that records rows and matches them back, so the skip path is exercised end to end rather than mocked. Covers skip on identical re-ingest, no skip on single-character change, per-profile scoping, empty-check returning None, row persistence with commit, full 64-char digest hashing, and database errors propagating instead of being swallowed.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** @kylipoo

Week 10 — Iteration & reflection
Reviewer feedback

Feedback received: [ ] Yes [x] No — no maintainer review this term (not a Summer 2026 feature). Peer review received and documented below.

Summary of feedback:
No maintainer or Copilot review requested changes on PR #305 (Copilot's four automated comments were a lockfile false-positive, an issue link that already resolves correctly, and two defensible design choices, none of which needed action). I did, however, get substantive peer feedback through the cohort. Kyle Li reviewed the PR and caught a real bug I had missed: _record_ingested_source called rollback() on a session that get_db() yields one-per-request, so on a database error it could have discarded a caller's pending writes while the swallowed exception still returned a successful-looking result.

How you responded:
I agreed and fixed it in commit e1496d7: dropped the rollback, let the SQLAlchemyError propagate so the session's owner decides how to handle a broken transaction, and added test_record_ingested_source_propagates_db_errors to pin the new behavior. On his second point, whether the record function should commit at all, I kept the commit and replied with the reasoning, that it matches how profile_service.py and review_service.py use the injected session, so it isn't surprising in context.

Reflection

What was harder than you expected?
The codebase fighting its own tooling was the surprise. On a clean checkout of main, make test-unit reports 53 failures, make check fails at ruff with 183 errors, and the pre-commit mypy hook fails with 12 more, none of it mine. The hard part wasn't the fix, it was proving my change was clean against that noise, which meant recording a baseline before I touched anything and framing every "passes" claim as "no new failures against 53" rather than a green run. A subtler version bit me early: make test-unit runs pytest -m unit, so my first test file was silently deselected and reported as passing while never executing, which is a worse failure than a red test because it looks like success.

What did you learn about working in a large codebase?
That the code is a set of claims to verify, not facts to trust. My Week 7 reviewer told me to check the real database schema rather than what the code assumed about it, and when I did, I found the IngestionPipeline referenced a source_id column that doesn't exist and review_service.py constructed IngestedSource with a raw_data= keyword matching no column on the model. The other lesson was scope discipline: that raw_data bug was tempting to fix, but it lived in a file issue #13 didn't name, so it went in the PR's Notes for Reviewers as an observed adjacent bug rather than widening my diff. Contributing to someone else's production code is as much about what you deliberately leave alone as what you change.

How did AI tools help — and where did they fall short?
AI was most useful as a reasoning and drafting partner: tracing the call binding through an async pipeline, drafting PLAN.md structure, and comparing a fix against the upstream original when I reviewed other students' PRs. Where it fell short was exactly where it sounded most confident. Reviewing another student's PR, the AI reasoned its way to a @staticmethod bug that would supposedly crash the instance path, and it sounded airtight. I ran the branch in an isolated git worktree and all 13 tests passed, so the bug didn't exist. That happened more than once, and the takeaway is that AI reasoning is a lead to verify by running the actual code, not a finding to repeat. The tool that suggested the bug is the same class of tool that can't tell you whether it's real, only the test run can.

What would you do differently if you started over?
I'd write my PLAN.md risks with their verification steps attached from the start. My Week 8 reviewer's one piece of forward feedback was to pair each risk with how to confirm it, so instead of "content_hash has no unique constraint" I'd write "confirm with \d+ ingested_sources that no unique index exists." I had actually run that check during the week; I just didn't record the command next to the claim, which is the difference between a risk a reviewer can validate in ten seconds and one they have to re-derive. I'd also reach for a worktree earlier when testing anything unfamiliar, since I wasted time cherry-picking mismatched files into my own checkout before switching to an isolated one.

What are you most proud of from this module?
The peer review exchange, more than the PR itself. I reviewed eight other students' PRs, and the reviews got sharper as I settled on a method: read the actual diff, verify the fix against the real code, check that tests exercise the real path rather than a mock returning canned values, and match the tone to the news. Catching that one student's docstring PR claimed eight documented functions across two files when one file was untouched from upstream, and that another's test asserted len(reviews) > 0 or len(reviews) == 0 which is always true, felt like the thing the whole module was actually teaching. And the loop with Kyle was genuinely mutual: he caught my rollback bug, I flagged his scope gap, and both of us shipped better work for it.