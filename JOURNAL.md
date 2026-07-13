## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/76

**Issue title:** POST /profiles returns HTTP 500 instead of HTTP 422 when the resume file is not a PDF

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the profiles page, when an uploaded resume file is not a PDF, the API returns a 500 Internal Server Error instead of a meaningful 422 Unprocessable Entity to indicate only PDFs are acceptable. The issue is in api/routes/profile.py, specifically in create_profile_endpoint. The docstring says the optional resume upload when creating a profile must be either PDF or Markdown, otherwise return 422. 

**Branch name:** fix/76-handle-pdf-validation-exception

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger