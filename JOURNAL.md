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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/janielcaday/pathreview/commit/8769cc4eabb82a244b426e4e51fa9231a365772d

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced the issue by simply starting up the app, and using one of the pre-seeded credentials who already have reviews completed. I observed that there was in fact *no* feature supported for retroactive review comparison.

**PLAN.md link:** https://github.com/janielcaday/pathreview/blob/feat/102-add-comparison-view/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]
N/A

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
- I will need to investigate database structure, whether reviews have a unique ID, how the code gathers all reviews associated with a user, etc. This is the primary foundation needed for figuring out how to add the comparison feature without breaking anything else in the repo.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Got sub-tasks 1-4 from PLAN.md mostly done. Added the compare route + entry point on ReviewHistoryPage (checkbox select + compare button), built out ComparisonView.tsx to pull both reviews and render them, and wrote the diffFormatter.ts logic to diff sections and score deltas. Also pulled some of the render logic into a new ComparisonSection.tsx component so ComparisonView isn't one giant file.

**Next steps:**
Need to write tests for diffFormatter (started the test file but not filled in yet), handle loading/error states properly, and cover the edge cases from PLAN.md (mismatched sections, pending reviews, <2 reviews).

**Blockers:**
None major, just need to double check how section_name matching behaves when agent output varies between reviews.

---

### Check-in 2 (end of week)

**PR link:** [Link to PR](https://github.com/janielcaday/pathreview/pull/1)

**Branch:** feat/102-add-comparison-view

**What you built:**
A before/after comparison view — users pick two completed reviews from ReviewHistoryPage, hit "Compare", and land on ComparisonView.tsx which shows overall score delta plus a per-section diff (added/removed/unchanged) computed by diffFormatter.ts.

**Tests added or updated:**
frontend/src/utils/__tests__/diffFormatter.test.ts — covers section diffing and score delta calc, including mismatched sections and identical-review edge case.

**Self-review confirmation:** [✓] make check passes  [✓] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [✓] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

No reviewer feedback was received/given.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**

Section matching uses exact section_name string match, so if wording drifts between review runs, sections show as fully added/removed instead of diffed — a known limitation, not fuzzy matching.

**What did you learn about working in a large codebase?**

I had to actually trace how reviews get stored and associated with a user before touching anything, instead of just building the UI first. In my own projects I'd usually wing it, but here breaking review history for existing users would've been bad. Also learned to lean on existing patterns (like how ReviewHistoryPage already fetched data) instead of reinventing my own fetch logic.

**How did AI tools help — and where did they fall short?**

AI was great for scaffolding — generating the ComparisonView.tsx skeleton, boilerplate for diffFormatter.ts, and test cases for straightforward scenarios. Fell short on the score-delta edge cases (mismatched sections, identical reviews) — those needed me to actually reason through the data shape myself and adjust the AI's first pass.

**What would you do differently if you started over?**

I'd plan for section-name drift up front instead of assuming exact string matches would hold. Right now diffSections keys sections by exact section_name, so if the agent phrases a section title even slightly differently between two review runs, it shows up as one section removed and a new one added instead of an actual diff. I'd rather have designed some fuzzy/normalized matching (lowercase, trim, maybe similarity threshold) from the start instead of realizing after the fact that exact-match was too brittle.

**What are you most proud of from this module?**

It was satisfying to see the whole thing come together end to end — from picking checkboxes on ReviewHistoryPage, through the diffing logic in diffFormatter.ts, all the way to a rendered comparison on ComparisonView.tsx. It's a small feature, but tracing it through every layer (data fetch, diff computation, UI) and having it actually work with real seeded review data felt like a solid full-stack win, especially since most of my day job is platform-side infra, not frontend feature work.