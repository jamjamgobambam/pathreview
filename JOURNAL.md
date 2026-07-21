# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference file, `docs/API.md`, lists the `POST /profiles` endpoint but
only gives it a one-line description. It never explains what you have to send in
the request, so anyone calling the API has to read the source code or open the
Swagger page to figure it out. The missing detail matters here because this
endpoint is not a normal JSON request — it takes a multipart form with three
optional fields: a GitHub username, a portfolio URL, and a resume file upload
(which must be a PDF or Markdown/plain-text file). A successful fix adds a clear
request body section for this endpoint — a table of the fields with their types
and rules, plus a short example request — so the doc on its own is enough to call
the endpoint correctly. The change only touches the documentation in `docs/API.md`
and does not change how the application behaves.

**Branch name:** docs/89-post-profiles-request-body

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
