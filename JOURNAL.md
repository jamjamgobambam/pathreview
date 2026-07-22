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