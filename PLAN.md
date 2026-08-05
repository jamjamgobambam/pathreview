## Solution plan

**Issue:** Add a before/after comparison view for users who have completed multiple reviews (#102)
**Link:** https://github.com/jamjamgobambam/pathreview/issues/102

### Understand
This is a feature gap rather than a bug. Currently, users have no built-in way to visualize their progress over time because the app only displays individual reviews in isolation. The expected behavior is that a user can select two distinct historical reviews and view a side-by-side comparison that explicitly highlights the differences in their scores and feedback.

### Map
Expected files to touch:
* `frontend/src/pages/ComparisonView.tsx` (New - Main UI component for the side-by-side layout)
* `frontend/src/utils/diffFormatter.ts` (New - Utility function to calculate score deltas and text differences)
* `frontend/src/App.tsx` (Existing - To register the new `/compare` route)
* `frontend/src/pages/DashboardPage.tsx` (Existing - To add a link/button routing users to the comparison feature)

### Plan
1. **Utility Creation:** Write `diffFormatter.ts` to accept two review data objects and return formatted diffs (e.g., calculating "+2" or "-1" for numerical scores, and identifying text changes). Write basic unit tests for this utility if the testing framework is already configured.
2. **Component Shell:** Create `ComparisonView.tsx` with a basic layout, including two dropdown selectors that allow the user to choose which past reviews they want to compare.
3. **UI Implementation:** Build the side-by-side visual layout within the component to render the data returned from `diffFormatter.ts`, utilizing existing UI components (like cards or tables) from the codebase.
4. **Routing & Navigation:** Add the new route to the application and place a "Compare Reviews" button on the user's main dashboard or review history list.

### Inputs & outputs
* **Inputs:** Two complete review objects (including numerical scores, written feedback, and timestamps) selected by the user.
* **Outputs:** A rendered React page displaying a visual differential—showing absolute scores for both dates, the calculated delta (e.g., green for improvement, red for regression), and side-by-side text boxes for feedback.

### Risks & unknowns
* **Data Fetching:** I need to investigate how a user's past reviews are currently fetched. Does the global state already hold all past reviews, or do I need to write a new API call to fetch a user's complete history?
* **Mobile Responsiveness:** A side-by-side view might become cramped and unreadable on smaller screens. I may need to stack the comparisons vertically on mobile breakpoints.

### Edge cases
* The user has only completed one review (the "Compare" button should be disabled or hidden).
* The user selects the exact same review for both the "Before" and "After" dropdowns.
* Older reviews might be missing data fields that newer reviews have, so `diffFormatter.ts` needs to handle `null` or `undefined` gracefully.