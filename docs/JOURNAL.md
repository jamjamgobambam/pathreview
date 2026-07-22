## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

When resume text is extracted from PDFs or pasted with indentation, section headers such as “Experience:” often sit at the start of a line with spaces before them. In ingestion/parsers/resume_parser.py, _detect_sections() matches headers only when they appear flush at the beginning of a line, so those indented headers are never recognized. Parsing still returns the full resume text, but metadata["detected_sections"] stays empty, which breaks expectations in the resume parser tests and any flow that relies on knowing which sections were found. A successful fix would allow optional leading whitespace on each line in those patterns so common sections are detected correctly and metadata lists them as intended.

**Branch name:**fix147-Resume-section-detection-fails-on-text-with-leading-whitespace 

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/8d7d12f414e3ffa7e3b22c8d7ff71c2c62e0ac3b

**Reproduction summary:**
I imported ResumeParser from ingestion.parsers.resume_parser and called parse() with the indented sample resume string from issue #147. metadata["detected_sections"] was [], matching the reported bug: section headers with leading whitespace are not detected.

**PLAN.md link:** https://github.com/JJC3321/pathreview/blob/fix/147-Resume-section-detection-fails-on-text-with-leading-whitespace/docs/plan.md

**Blockers or open questions:**
None