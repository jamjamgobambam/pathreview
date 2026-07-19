# PathReivew – JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/102

**Issue title:** Add a before/after comparison view for users who have completed multiple reviews
- Issue description: https://github.com/ascherj/pathreview/issues/102#issue-4117413267

**Tier:** [ ] Tier 1  [ ] Tier 2  [✓] Tier 3 

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of the title), what is currently broken or missing, and what a successful fix would accomplish. Naming the part of the codebase it affects is helpful context.]
For users who have completed multiple reviews, they might want to view their progress between two reviews. Adding a comparison view would allow the user to select two exiting reviews, and initiate a comparison review between the two. The comparison review would cover metrics, whether stats went up or down in certain areas, and maybe even what exactly was submitted in said reviews. I haven't looked into the codebase too much yet, but showing previous state might be out of scope for this issue since we would need to save what was submitted into a database, and call it back when a comaprison review is triggered. As for the part of the codebase it affects, we would need to make a new page, `frontend/src/pages/ComparisonView.tsx` for a user-friendly UI, and `frontend/src/utils/diffFormatter` to fill in elements, calculate statistical differences, etc. I am a platform engineer during the day, and creating new frontend tooling aligns with my skillset.

**Branch name:** feat/102-add-comparison-view

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger