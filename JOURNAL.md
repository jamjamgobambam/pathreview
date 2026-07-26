## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/69

**Issue title:** Add a "feedback tone check" that ensures all generated feedback is written constructively

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
After PathReview generates feedback for a user, there is currently no check on whether that feedback is written constructively. This issue asks for a tone classification step to run after generation, using a prompt to judge whether each feedback section is constructive (actionable, specific, encouraging) or negative (discouraging, vague, dismissive). Sections that fail the check should be rejected and regenerated rather than shown to the user. The main files affected are `safety/content_filter.py` and `rag/generator/review_generator.py`, so the fix touches both the safety layer and the review generation pipeline.

**Branch name:** feat/69-feedback-tone-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger