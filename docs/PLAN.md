## Solution plan

**Issue:** [Add accessibility tests for the review page using `jest-axe`](https://github.com/ascherj/pathreview/issues/105)

### Understand
The root cause of this issue is a test-coverage gap. ReviewPage.tsx and all 6 pages have no test files. The lack of tests means we have no way to ensure any future changes to the code will not regress existing behavior or to confirm that the code works as intended. Although all of the pages need unit tests covering both logic and A11y, the scope of this issue is to add A11y tests for ReviewPage.tsx.

Expected behavior: An automated axe scan passes in every render state and every interactive element is reachable by role and accessible name.

Actual behavior: No tests exist

### Map
This issue is rather self-contained resulting in all edits made to `frontend/src/pages/__tests__/ReviewPage.test.tsx` and a one-line addition to `frontend/src/test/setup.ts`. I will be reviewing and pulling in objects relevant to `frontend/src/pages/ReviewPage.tsx` but no edits to the component.

### Plan
1. Read `frontend/src/pages/ReviewPage.tsx` and identify which areas of the code need tests
2. Create `frontend/src/pages/__tests__/ReviewPage.test.tsx` 
3. add the `jest-axe` matcher to `frontend/src/test/setup.ts`
4. Create helpers and mock objects needed for ReviewPage in the test file
5. Create a section for semantic/ role assertions and add tests to it
-- Ex: assert getByRole('button', {name: "text-name"})
6. Run `npm test` to verify
7. Create a section for axe scans like loading and DOM states and add tests to it
8. Run `npm test` to verify

### Inputs & outputs
Input: mocked objects and API return values

Something like:

```tsx
it('complete state has no axe violations', async () => {
  vi.mocked(useReviewStatus).mockReturnValue({ review: {...}, isPolling: false, error: '' })
  vi.mocked(apiClient.getReview).mockResolvedValue(fixtureReview)
  const { container } = renderWithRouter(<ReviewPage />)
  await screen.findByRole('heading', { name: /portfolio review/i })
  expect(await axe(container)).toHaveNoViolations()
})
```

Output: A suite of tests
- I don't guarantee that they all pass as there may be existing broken functionality or gaps

### Risks & unknowns
This issue is well scoped. The main unknown would come from existing functionality gaps. While skimming ReviewPage, I noticed the score progress bar has no role for screen readers to query by. I can either include a test for it expecting it to fail and leave a comment for an issue to be created for it or leave it out of scope.

I recommend leaving it out of scope and creating a TODO for someone to improve the accessibility of the score progress bar. 

### Edge cases
The edge cases are testing the render states. The states I was able to identify were:
- loading (isPolling)
- complete (main, "happy", path)
- overall_score === undefined (score block hidden)
- sections empty (fallback text)
- failed with vs without error_message (tests the || conditional fallback)
- error banners (error / fetchError related to the spinner)

One thing to note is A11y testing does not check business logic but the accessibility of the component.
