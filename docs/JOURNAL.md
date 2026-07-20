## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/101)

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
There is currently no way for a user to share their review summary with someone who 
doesn't have an account. This issue asks for a shareable link that renders a read-only 
version of the review page without requiring login, and that link should stop working 
after 30 days. It touches ReviewPage.tsx and a new shareService.ts on the frontend, 
and the reviews API route on the backend. So it needs a new endpoint to generate/store 
a share token, a public endpoint to serve the shared view, and a UI entry point 
(the copy-link button) to trigger it.

**Branch name:** feat/101-shareable-review-link

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger