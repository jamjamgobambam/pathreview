## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/105

**Issue title:** Add accessibility tests for the review page using jest-axe

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review page currently does not have automated accessibility coverage, so regressions like invalid ARIA attributes, missing labels, or heading problems could be introduced without being caught by the frontend test suite. This issue asks for tests around `ReviewPage` using `jest-axe`, while following the project's existing Vitest and React Testing Library patterns. The relevant code is in the frontend, especially `frontend/src/pages/ReviewPage.tsx`, `frontend/src/test/setup.ts`, and possibly `frontend/src/components/ReviewSection.tsx` if the accessibility test exposes a real issue. A successful fix will add focused accessibility tests and only change production code if the tests reveal a genuine accessibility violation.

**"Is this right for me?" checklist reasoning:**
I chose this issue because the scope is realistic and mostly limited to the frontend test setup and a new ReviewPage test file. The repository already uses Vitest, React Testing Library, jsdom, and has `jest-axe` listed in the frontend dev dependencies, so the required testing infrastructure is mostly present. I inspected the ReviewPage and related components and found that ReviewPage depends on router params, `useReviewStatus`, and `apiClient.getReview`, which can be mocked in tests. The main risk is that axe may expose an accessibility issue in `ReviewSection`, but the plan is to keep production changes minimal and only fix that component if the test shows a real violation.

**Branch name:** test/105-review-page-accessibility-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
