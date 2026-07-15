## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/105

**Issue title:** Add accessibility tests for the review page using `jest-axe`

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review page (`frontend/src/pages/ReviewPage.tsx`) has no automated
accessibility checks, so regressions like poor color contrast, missing form
labels, or broken heading hierarchy can slip in unnoticed. The fix adds
`jest-axe`-based tests in `frontend/src/pages/__tests__/ReviewPage.test.tsx`
that render the page and assert it has no detectable a11y violations. This
gives the frontend a regression net for accessibility on one of the app's
core screens.

**Branch name:** test/105-review-page-accessibility-tests

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger