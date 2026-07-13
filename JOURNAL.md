# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There is no route-level test coverage anywhere in the API — not just for this
endpoint, but for any endpoint in the app. `POST /reviews` accepts a profile_id
and immediately returns a pending review with no check that the profile actually
has any ingested content (GitHub username, portfolio URL, or resume). The
background task that's supposed to process the review is currently built from
placeholder logic, so a profile with zero ingested sources doesn't error out —
it silently produces a fake "complete" review with fabricated content and a
canned score. A successful fix adds an upfront validation check that rejects
profiles with no ingested content, and a new test file (the first route-level
test file in the repo) verifying that behavior.

**Scope reasoning:** [work through your course's "Is this right for me?"
checklist here — e.g. estimated effort vs. your available time, whether you
understood the affected code before claiming it, whether the issue was still
valid (verified above).]

**Branch name:** test/88-review-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
