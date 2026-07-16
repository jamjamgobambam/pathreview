## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/6

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** Tier 2  

**Problem summary:**
Right now, the app can ingest the same GitHub repository more than once and store repeated embeddings for the same content. This makes retrieval less reliable because duplicate chunks can show up as if they are more important than they really are. The fix should make repo ingestion recognize already-processed sources and avoid adding duplicate vector entries.

**Tier and scope reasoning:**
This scope feels like a good fit for me because it is focused enough to complete, but still pushes me to trace how data moves through the ingestion pipeline, database model, and vector store. I have already located the main files involved, so I can work from a clear starting point instead of trying to understand the whole app at once. It also feels realistic for the Week 8-9 timeline because the goal is specific: prevent duplicate ingestion and prove the behavior with targeted tests.

**Branch name:** fix/6-duplicate-embeddings-error

**Setup confirmation:** ✅ App runs locally at localhost:5173

**Cohort ledger:** ✅ Issue added to cohort ledger
