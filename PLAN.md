## Solution plan

**Issue:** [Add a "Copy link" button to share a public review summary](https://github.com/ascherj/pathreview/issues/101)

### Understand

The review detail page (`frontend/src/pages/ReviewPage.tsx`) has a "Share" button that calls `handleShare`, which writes `window.location.href` to the clipboard and confirms with a blocking `alert()`. There is no dedicated "Copy link" button with inline, non-blocking feedback. To verify this, I ran the failing reproduction tests — both assert `role="button" and name /copy link/i` — and the DOM output printed by the test runner confirmed only two buttons exist on the page: "Share" (with a Share2 icon) and "Export". No "Copy link" button is present anywhere in the rendered output.

The expected behavior: a clearly labeled "Copy link" button that copies the review URL to the clipboard and shows a transient "Copied!" confirmation inline, without blocking the UI.

### Map

Files I expect to touch:

- `frontend/src/pages/ReviewPage.tsx` — replace the existing `handleShare` / "Share" button with a "Copy link" button that shows inline "Copied!" feedback using a `useState` timer
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` — update the reproduction tests to pass once the button exists, and add a test for the "Copied!" feedback state
- No backend changes needed — the review URL is already the public route `/reviews/:reviewId` and the existing `GET /reviews/{review_id}` endpoint is sufficient for this scope

### Plan

1. Add a `copied` boolean state to `ReviewPage` and a `handleCopyLink` function that calls `navigator.clipboard.writeText(window.location.href)` and sets `copied` to `true` for 2 seconds via `setTimeout`
2. Replace the "Share" button JSX with a "Copy link" button that renders "Copy link" normally and "Copied!" when `copied` is `true`, using the `Link` or `Check` icon from lucide-react
3. Update `frontend/src/pages/__tests__/ReviewPage.test.tsx` to assert the button renders, copies the URL, and shows "Copied!" feedback after click
4. Run `npx vitest run src/pages/__tests__/ReviewPage.test.tsx` and confirm all tests pass

### Inputs & outputs

- Input: user clicks "Copy link" on a completed review page
- Output: `navigator.clipboard.writeText` is called with the current page URL; the button label changes to "Copied!" for 2 seconds then reverts to "Copy link"

### Risks & unknowns

- `navigator.clipboard` is only available in secure contexts (HTTPS or localhost) — the jsdom test environment requires mocking it, which the reproduction test already does; no risk in production since the app runs on localhost in dev and should be served over HTTPS in production
- The existing "Share" button has no `aria-label`, so removing it and replacing with "Copy link" is a clean swap with no accessibility regression — but worth double-checking that the new button has accessible text
- If the issue acceptance criteria require a *public* shareable link (i.e. unauthenticated access), that would require a backend token — the current `GET /reviews/{review_id}` endpoint in `api/routes/reviews.py` requires `get_current_user`. This is the main unknown: the issue title says "public review summary" but the simplest interpretation is just copying the current authenticated URL. I'll implement the frontend-only version first and note this in the PR.

### Edge cases

- Clipboard API unavailable (non-secure context, old browser): wrap `navigator.clipboard.writeText` in a try/catch and fall back to a visible URL input the user can copy manually
- Button clicked multiple times rapidly: the `setTimeout` should be cleared and reset on each click to avoid the label flickering back prematurely
- Review not yet complete: the "Copy link" button should only render when `fullReview.status === 'complete'`, which is already gated by the existing conditional in `ReviewPage.tsx`
