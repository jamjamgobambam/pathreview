# Pathreview - PLAN.md

## Solution plan

**Issue:** [Add a before/after comparison view for users who have completed multiple reviews](https://github.com/ascherj/pathreview/issues/102)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Users may want to view their progress, or compare past reviews with more recent reviews. The current issue is that Pathreview has no support for this. Expected behavior is that there IS support, and actual behavior is that there is NO support.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The below files are completely new files that need to be added in order to support this feature.
- frontend/src/pages/ComparisonView.tsx
- frontend/src/utils/diffFormatter.ts

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Add `/reviews/compare` route + entry point (e.g. "Compare" button on ReviewHistoryPage, enabled when 2+ reviews selected via checkboxes), wired to `ComparisonView.tsx`.
2. In `ComparisonView.tsx`, read two review IDs (older/newer) from route state or query params, fetch both full reviews via `apiClient.getReview(id)`.
3. Build `diffFormatter.ts`: given two `Review` objects, produce a per-section diff — matched by `section_name`, with score delta and content/suggestions diff (added/removed/unchanged lines).
4. Render comparison UI: side-by-side or unified before/after layout, overall score delta banner, per-section diff using `diffFormatter` output, reusing `StatusBadge`/`ReviewSection`-style components where reasonable.
5. Handle loading/error states for both reviews and add basic tests for `diffFormatter.ts`.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
**Input:** two review IDs (older review, newer review) for the same profile, obtained from `apiClient.getReview(id)`.
**Output:** a rendered comparison page showing overall score delta and a per-section text/suggestion diff; no backend or data model changes required — purely a new frontend page + formatting util consuming existing `Review` API responses.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- Section names may not match exactly between two reviews (agent output can vary), so diffing "by section_name" may leave orphan sections on either side.
- No existing multi-select UI on ReviewHistoryPage — will need a function to check if there are more than two existing reviews associated with the profile and add selection state without breaking existing table/pagination behavior.

### Edge cases
What inputs or states should your fix handle gracefully?
- Fewer than 2 completed reviews available (disable/hide compare entry point).
- One or both reviews still `pending`/`failed` (we should block comparison for this).
- Reviews with mismatched sections (section present in one but not the other).
- Identical reviews (no diff / "no changes" state).