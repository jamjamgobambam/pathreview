## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/18

**Issue title:** Add end-to-end ingestion test with a sample resume fixture

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The pipeline that ingests a resume — from file upload through parsing and into embedding storage — currently only has unit tests for individual parser components in isolation. There's no test verifying the full chain works together end-to-end. This issue asks for an integration test in `tests/integration/test_ingestion_pipeline.py` that uses existing sample resume fixtures in `tests/fixtures/sample_resumes/` to confirm a resume can be uploaded, parsed, embedded, and stored correctly in one continuous flow.

**Branch name:** test/18-e2e-ingestion-pipeline

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Sniggy26/pathreview/commit/c9cc479

**Reproduction summary:**
Confirmed via a direct Python script that `IngestionPipeline.ingest_resume()` already works end-to-end (parse → chunk → embed → store) when called directly, producing 1 chunk and storing it in a real ChromaDB collection. Also discovered the pipeline is never actually called from the API's resume upload endpoint, and that its dedupe-check and DB-recording methods are unfinished placeholders.

**PLAN.md link:** https://github.com/Sniggy26/pathreview/blob/test/18-e2e-ingestion-pipeline/PLAN.md

**Walkthrough video (recommended):** [not recorded this week]

**Blockers or open questions:**
Need to decide whether to build a proper test DB session fixture or use a lightweight fake for the `db_session` argument, since no Postgres-backed test fixture currently exists in `tests/conftest.py`. Also unsure whether the skip/dedupe test should assert current (buggy) behavior or flag it as a known gap without asserting on it.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/588

**Branch:** test/18-e2e-ingestion-pipeline

**What you built:**
An end-to-end integration test (`tests/integration/test_ingestion_pipeline.py`) covering the full resume ingestion chain — parse → chunk → embed → store — by calling `IngestionPipeline.ingest_resume()` directly against a real in-memory ChromaDB collection and a `MockEmbeddingProvider`. Along the way I found and documented two real cross-component bugs (an empty-metadata-list crash triggered by indented resume text, and a broken dedupe check) that unit tests alone hadn't caught.

**Tests added or updated:**
Added `tests/integration/test_ingestion_pipeline.py` with 3 tests: `test_ingest_resume_end_to_end` (happy path, asserts real storage via `collection.count()`), `test_ingest_resume_no_experience_section` (edge case with no Experience section), and `test_ingest_resume_duplicate_content_does_not_dedupe_today` (documents current dedupe behavior). Also added a fixture file at `tests/fixtures/sample_resumes/sample_resume.md`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass in the sense defined by the assignment: no new failures introduced. `make test-unit` shows the same pre-existing 53 failures/375 passing before and after this PR. `make check`'s mypy step cannot complete on any file in the repo, including files untouched by this PR, due to a pre-existing `python_version`/numpy stub mismatch — documented in the PR and commit message. `ruff` and `black` both pass cleanly on my new file.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback has come in yet on PR #588 as of this writing. Per the assignment note, reviewer feedback isn't a live feature for Summer 2026, so this is expected rather than a gap on my end.

**How you responded:**
N/A — nothing to respond to yet. If feedback comes in after submission, I'll follow up in the PR thread and note the exchange here if I'm able to edit this file further.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running was far harder than actually writing the test. I hit a real version conflict where the pinned `chromadb:0.4.22` Docker image auto-installed a newer numpy at container startup, but Chroma's own code still used the removed `np.float_` attribute, crashing the vector-db container outright. I had to override the container's entrypoint command to force-install `numpy<2.0.0` before the server started. I also didn't have Homebrew, Node, or Docker installed at the start of this module, so a huge chunk of my actual time went into infrastructure, not code — something I hadn't budgeted for when I first read the assignment.

**What did you learn about working in a large codebase?**
The biggest lesson was that my assumptions about how components interact were often wrong, and the only way to know was to run the code. For example, I assumed `IngestionPipeline.ingest_resume()` was wired up to the actual resume upload endpoint in `api/routes/profiles.py` — it isn't; that route parses resumes independently via raw `PyPDF2` and never calls the pipeline at all. I only found that by grepping the whole repo for `IngestionPipeline` usage. I also learned that "it has unit tests" doesn't mean the pieces work together — my e2e test surfaced a real crash (empty `detected_sections` list breaking ChromaDB's metadata validation) that no individual parser test caught, because it only showed up when parsing output flowed into the embedding/storage step.

**How did AI tools help — and where did they fall short?**
Claude was most useful for fast code navigation — pointing me at suspicious lines (like the `_check_skip()` placeholder query) and helping me write reproduction scripts quickly so I could verify behavior instead of guessing. But it also got things wrong at first: when I was investigating the "duplicate search results" bug earlier in the project, Claude's first hypothesis (that a SQL join was fanning out per tag) turned out to be false once I actually ran the query and checked `len(results)` myself. That was a useful reminder that AI-generated hypotheses need verification against real output, not just plausible-sounding reasoning — which is exactly the discipline this module was trying to teach in the first place.

**What would you do differently if you started over?**
I'd read more of the surrounding pipeline code (`batch_processor.py`, `provider.py`) before writing my first reproduction script, rather than writing the script first and discovering the actual API shapes as I went. I'd also set up Docker, Homebrew, and Node right at the start of Module 3 instead of only installing them when `make setup` failed, since that environment work ended up eating time I'd rather have spent on the actual test logic.

**What are you most proud of from this module?**
Finding and clearly documenting two real, previously-unknown bugs (the indented-text section-detection crash, and the broken `_check_skip` dedupe logic) instead of just writing a test that technically passed. It would have been easy to write a shallow happy-path test and call it done; instead the test genuinely proved something true and useful about the codebase, which is what an integration test is supposed to do.