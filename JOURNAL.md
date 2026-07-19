## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/105

**Issue title:** Add accessibility tests for the review page using `jest-axe`

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review page (`frontend/src/pages/ReviewPage.tsx`) has no automated
accessibility checks, so regressions like poor color contrast, missing form
labels, or broken heading hierarchy can slip in unnoticed. The page renders
different DOM depending on state — polling/loading, failed, and complete —
so an a11y violation could exist in one state and not another. The fix adds
`jest-axe`-based tests in `frontend/src/pages/__tests__/ReviewPage.test.tsx`
that render each of these states and assert none has detectable a11y
violations. This gives the frontend a regression net for accessibility
across the full lifecycle of one of the app's core screens.

**Acceptance checklist:**
- [ ] `jest-axe`'s `toHaveNoViolations` matcher wired into the test setup
- [ ] Test renders the polling/loading state and asserts zero axe violations
- [ ] Test renders the failed state and asserts zero axe violations
- [ ] Test renders the complete state (with review sections) and asserts zero axe violations
- [ ] All new tests pass via `make test-unit`

**Why this issue fits (scope-fit reasoning):**
- Tier 2, 4–6h estimated effort — matches what I can commit this week
- `jest-axe` is already a devDependency in `frontend/package.json`, so no new
  tooling setup is required, just test code
- The repo already has React Testing Library test patterns to follow
  (`ProfileForm.test.tsx`, `ReviewSection.test.tsx`), so I'm extending an
  established pattern rather than inventing one
- Scope is one new file (`ReviewPage.test.tsx`); no backend, API, or
  component changes needed, keeping blast radius small
- `useReviewStatus` is a mockable hook, so all three render states can be
  driven in tests without a live backend

**Branch name:** test/105-review-page-accessibility-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger