# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/69

**Issue title:** Add a "feedback tone check" that ensures all generated feedback is written constructively

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now the review generator produces feedback sections with no check on how they read — a section could come out vague, discouraging, or dismissive and still go straight to the user. This issue asks for a tone classification step that runs after generation, using a prompt to judge whether each section is constructive (actionable, specific, encouraging) or not. Sections that fail the check should be rejected and regenerated rather than shown to the user. The fix touches the safety layer (`safety/content_filter.py`) and the generation pipeline (`rag/generator/review_generator.py`), since it needs to hook into the point where feedback sections are produced.

**Branch name:** feat/69-feedback-tone-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
