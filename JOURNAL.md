## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

I picked Tier 2 because I have previously built RAG pipeline and I can mirror existing pipline for resume to build new feature

**Problem summary:**
The is no existing ingestion pipeline for the portfolio submitted through the URL. The successful implemention would fetch the page content, extract relevant text (bio, project descriptions), and include it in the vector store. The parts of database that are involved: 
ingestion/parsers/ (new web_parser.py)
ingestion/pipeline.py
api/schemas/profile.py

**Branch name:** feat/11-portfolio-url-ingestion

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Tanya703/pathreview/commit/67149a3d194a6364d27765e0a0f69f7120b34eb3

**Reproduction summary:**
I added `tests/unit/test_web_parser.py`, which imports `ingestion.parsers.web_parser.WebParser` and calls `IngestionPipeline.ingest_portfolio(...)`. Running `pytest tests/unit/test_web_parser.py -v` confirmed the gap: the import fails with `ModuleNotFoundError: No module named 'ingestion.parsers.web_parser'`, and the pipeline test fails with `AssertionError` because `IngestionPipeline` has no `ingest_portfolio` method. This confirms that although the UI, API, and DB already accept and store a profile's `portfolio_url`, nothing ever fetches or ingests that page's content into the vector store.

**PLAN.md link:** https://github.com/Tanya703/pathreview/blob/feat/11-portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
When I tried replicating the issue through the UI, I couldn't see any ingested sources in the database after submitting a new profile — but all the info was saved correctly in `profiles`.  Is there a bug? Typeerror with ingestion? 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I have implemented a Webparser part: 1. Write `WebParser` — fetch the URL, strip boilerplate, pull out the readable text

**Next steps:**
[What are you working on for the rest of the week?]
I am looking to get steps done:
2. Add `ingest_portfolio` to the pipeline, following the same shape as `ingest_resume`
3. Hook it into `profile_service.py` so saving a profile with a portfolio URL kicks off ingestion
4. Make `_record_ingested_source` actually write to the DB instead of just logging, so dedup works
5. Turn the reproduction stubs in `test_web_parser.py` into real tests

**Blockers:**
[Anything slowing you down? Or leave blank.]
I need to figure out all files I need to update and add URL ingestion

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/450

**Branch:** feat/11-portfolio-url-ingestion


**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I build a portfolio URL ingestion: a new WebParse that fetches porfolio page and extracts text and an ingest_portfolio method that runs tesx through the same chenk and embed flow. I wired this into profile_service.py so saving a profile with a portfolio_url automatically triggers ingestion in the background, failing quietly if the site is down or unparseable. You also fixed _record_ingested_source/_check_skip to actually read and write the IngestedSource table.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
14 tests were added
WebParser.parse() is tested for extracting readable text from portfolio HTML, stripping script/style/nav boilerplate, capturing title and word-count metadata, handling bytes input, and rejecting invalid content types. WebParser.fetch() is tested for a successful fetch, an HTTP/connection error, and a non-HTML content type, all raising ValueError appropriately. IngestionPipeline.ingest_portfolio() is tested end-to-end (fetch → parse → chunk → embed → DB record), for skipping re-ingestion of unchanged content (dedup), and for propagating exceptions when a fetch fails.

**Self-review confirmation:** [ x] make check passes  [x ] make test-unit passes

**Draft PR feedback received from:**  "none"