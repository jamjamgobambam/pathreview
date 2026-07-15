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

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger