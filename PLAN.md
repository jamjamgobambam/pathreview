## Solution plan

**Issue:** Add accessibility tests for the review page using `jest-axe` ([#105](https://github.com/ascherj/pathreview/issues/105))

### Understand
Not a bug — a test gap. `ReviewPage` (`frontend/src/pages/ReviewPage.tsx`)
has no automated accessibility coverage, so violations (missing labels,
bad heading order, insufficient contrast) could ship unnoticed. Expected:
`jest-axe` tests exist and run in CI, asserting zero violations. Actual:
zero a11y tests for this page today. Root complication is that the page
isn't one static tree — it conditionally renders one of three states
(polling, failed, complete) plus optional error banners, so "the page has
no violations" has to be checked per state, not once.

### Map
- `frontend/src/pages/ReviewPage.tsx` — component under test, 3 render
  branches driven by `isPolling`, `currentReview?.status === 'failed'`,
  `fullReview?.status === 'complete'`
- `frontend/src/hooks/useReviewStatus.ts` — polling hook; needs mocking to
  force each state deterministically
- `frontend/src/services/api.ts` (`apiClient.getReview`) — fetched once
  status is `complete`; needs mocking
- `frontend/src/types.ts` — `Review` / `FeedbackSection` shapes for fixtures
- New file: `frontend/src/pages/__tests__/ReviewPage.test.tsx` (dir doesn't
  exist yet, confirmed via `ls`)
- Reference patterns: `frontend/src/components/__tests__/ProfileForm.test.tsx`
  (`vi.mock` on a hook) and `ReviewSection.test.tsx` (RTL + vitest style)

### Plan
1. Create `frontend/src/pages/__tests__/ReviewPage.test.tsx`, wrap render in
   a router context (`MemoryRouter` with a `:reviewId` route, or mock
   `useParams`/`useNavigate` from `react-router-dom`) since `ReviewPage`
   calls both directly.
2. `vi.mock('../../hooks/useReviewStatus')` and `vi.mock('../../services/api')`,
   following the `ProfileForm.test.tsx` pattern, so each test can force a
   specific `{ review, isPolling, error }` shape without a real backend.
3. Write one `jest-axe` case per state: polling (`isPolling: true`), failed
   (`status: 'failed'`, with `error_message`), complete (`status: 'complete'`
   with `overall_score` and populated `sections` so `ReviewSection` also
   renders) — each asserts `expect(await axe(container)).toHaveNoViolations()`.
4. Add a case for the error-banner paths (`error` from the hook, and
   `fetchError` from a failed `getReview` call) since those inject extra DOM
   (`role`/live-region considerations) on top of whichever base state is active.
5. Wire `jest-axe`'s matcher (`toHaveNoViolations`) into test setup if not
   already global, run `make test-unit` / `npm test`, confirm all pass.

### Inputs & outputs
Input: mocked `useReviewStatus` return values and mocked `apiClient.getReview`
resolved/rejected values, one fixture per state. Output: new test file with
no production code changes; CI gains a permanent regression check that fails
loudly if a future edit introduces an a11y violation in any of the three states.

### Risks & unknowns
- `useEffect` in `ReviewPage` fires `getReview` async — tests need
  `await`/`findBy*` or `waitFor` around the axe check for the complete state,
  or the DOM snapshot could be checked mid-fetch.
- Unsure whether `jest-axe`'s matcher is already registered globally
  (e.g. in a `setupTests` file) or needs adding per-file — check
  `vite.config.ts`/`vitest.config.ts` `setupFiles` before assuming.
- Router mocking approach (`MemoryRouter` vs. mocking `react-router-dom`)
  affects how much boilerplate each test needs — pick whichever the existing
  tests already lean toward, for consistency.
- Tailwind color-contrast violations are common false-negatives/positives
  with jsdom (no real rendering) — `jest-axe` may not catch contrast issues
  at all in this environment; scope expectations accordingly.

### Edge cases
- Both `error` (from polling) and `fetchError` (from `getReview`) present at
  once — two error banners stacked.
- `complete` status but `fullReview.sections` empty/undefined — renders the
  "No feedback sections available" fallback text instead of `ReviewSection`s.
- `complete` status but `overall_score` undefined — score block should not
  render at all (conditional at line 131).
- Transition moment where `statusReview` is `complete` but `fullReview` is
  still `null` (fetch in flight) — falls through all three branches, renders
  just the back button; still must have zero violations.