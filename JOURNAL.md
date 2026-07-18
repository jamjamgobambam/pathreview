## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Right now, PathReview can ingest data from a resume, a GitHub profile, and repos. This issue adds a fourth source: a user's personal portfolio website. The user pastes a URL like https://janedoe.dev, and the system should fetch that web page, pull out the meaningful text (their bio, project write-ups), and feed it into the same "vector store" that powers the AI feedback. This allows the AI to reference their portfolio when reviewing them.

I would have to add an ingest_portfolio() method that mirrors the existing ingest_resume / ingest_readme methods almost line-for-line: generate a source_id, check-if-already-ingested, call the new parser, chunk, embed, and record. 

**Branch name:** feat/11-ingesting-portfolio-website-URL                                                    

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger