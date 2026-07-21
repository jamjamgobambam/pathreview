## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API documentation in `docs/API.md` describes each endpoint but lacks example
`curl` commands. This makes it harder for developers setting up the project for
the first time to quickly verify that the API is working. A successful fix will
add copy-pasteable `curl` examples for each documented endpoint, matching the
current API routes and keeping the existing formatting consistent. The change
lives entirely in `docs/API.md` and doesn't require modifying any application code.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

### "Is this issue right for me?" – Checklist & Reasoning

#### Part 1 — Understanding the Issue
- [X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.  
  *The API docs are incomplete; they describe endpoints but don't show how to call them with `curl`. Adding examples will make it easier for anyone to test the API locally.*
- [X] I've located the relevant files and confirmed they exist in the codebase.  
  *The file is `docs/API.md` – I found it in the repo root.*
- [X] I can describe a concrete before-and-after.  
  *Before: the docs show endpoint paths and descriptions, but no `curl` commands. After: each endpoint has a working `curl` example that can be copied and run immediately.*

#### Part 2 — Tier Fit
- [X] I'm choosing Tier 1 because this is my first contribution to a large codebase.  
  *The change is scoped to one file, doesn't involve complex logic, and I can test the examples against my local API.*

#### Part 3 — Codebase Readiness
- [X] I've found and read the specific code the issue references.  
  *I opened `docs/API.md` and saw the existing structure; I also explored the API at `http://localhost:8000/docs` to know which endpoints exist.*
- [X] I've read enough surrounding context that I can write a rough plan for the fix.  
  *I'll add a new `### Example` subsection under each endpoint, with a `curl` command that uses the local `http://localhost:8000` base URL and includes the necessary headers and JSON payloads.*
- [X] I've found the test file for my module and read at least one test end-to-end.  
  *This is a documentation change, so no tests are required, but I verified the API behavior manually using Swagger.*

#### Part 4 — Scope and Time
- [X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.  
  *The issue has no other claimed students yet, so I have a clear path.*
- [X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.  
  *Estimated 2–3 hours: read docs, write curl commands, test each, update the file, run `make check`, open PR.*
- [X] This issue has no open blockers or dependencies on other unresolved issues.

**Verdict:** I'm ready to claim this issue.