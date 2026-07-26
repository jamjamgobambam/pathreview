## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/69

**Issue title:** Add a "feedback tone check" that ensures all generated feedback is written constructively

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now, PathReview generates feedback for users without checking whether the tone is constructive. This means the app could produce feedback that reads as harsh or discouraging without any safeguard catching it before it reaches the user. This issue asks for a tone check step added to the feedback generation pipeline, likely inside the review or agent logic, that verifies generated feedback is written supportively and flags or rewrites anything that isn't. A successful fix ensures every piece of feedback shown to a user is honest but constructive in tone.

**Branch name:** feat/69-feedback-tone-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger