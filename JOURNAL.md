## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/11)]

**Issue title:** [Add support for ingesting a portfolio website URL]

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now the ingestion pipeline only pulls in data from GitHub and resumes, so it has no way to capture context that only lives on a candidate's personal portfolio site, like project write-ups or bio copy. This means the vector store is missing potentially valuable signal about a person's work that they've chosen to showcase outside of GitHub. The fix requires adding a new web parser (likely `ingestion/parsers/web_parser.py`) that fetches a submitted portfolio URL, scrapes the page, and extracts relevant text such as bio and project descriptions. That extracted content then needs to be wired into `ingestion/pipeline.py` so it's embedded and stored alongside the existing GitHub/resume data, and `api/schemas/profile.py` needs to be updated so the API can accept and validate a portfolio URL field on a profile submission.

**Branch name:** [feat/11-add-support-for-ingesting-portfolio-website-url]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger