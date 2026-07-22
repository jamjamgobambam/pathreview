# Module 3 Journal — LaxmiPrasanna Ravikanti

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/101

**Issue title:** Add a "Copy link" button to share a public review summary

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
<!-- TODO: Rewrite this in YOUR OWN WORDS before submitting — "in your own words"
     is a grading criterion, and identical/AI-sounding phrasing can be flagged.
     The draft below is accurate; make it sound like you and confirm you understand it. -->
Right now PathReview only lets a logged-in user view their own review summary —
there is no way to share it with someone who does not have an account. This issue
asks for a "Copy link" button on the review page that produces a shareable URL to a
read-only version of the summary. The link must open without requiring a login and
must stop working after 30 days. A successful fix spans the whole stack: a new
frontend service (`shareService.ts`) to request the link, a button wired into
`ReviewPage.tsx`, and a backend endpoint in `api/routes/reviews.py` that creates and
validates time-limited public share tokens.

**Branch name:** feat/101-share-review-link

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
<!-- TODO: Add your name, GitHub username (prasanna-4), and issue #101 to your
     section's tab in the cohort issue ledger, then check this box. -->

### "Is this right for me?" — scope reasoning
<!-- TODO: Work through the actual "Is this right for me?" checklist linked in the
     Module 3 resources and note your real reasoning here. Notes below are a start. -->
- **Tier / effort:** Tier 2, estimated 5–8 hours. More involved than a Tier 1 bug fix.
- **Surface area:** Touches three layers — React frontend (`ReviewPage.tsx`), a new
  frontend service (`shareService.ts`, which does not exist yet), and the Python API
  (`api/routes/reviews.py`). It is a full-stack feature, not a contained fix.
- **Key design decisions:** how to generate a public share token, where to store it,
  and how to enforce the 30-day expiry and no-login read-only access.
- **Why I think I can do it / risks to watch:** <!-- TODO: your own assessment -->
