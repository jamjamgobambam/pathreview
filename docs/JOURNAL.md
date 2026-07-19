## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

When resume text is extracted from PDFs or pasted with indentation, section headers such as “Experience:” often sit at the start of a line with spaces before them. In ingestion/parsers/resume_parser.py, _detect_sections() matches headers only when they appear flush at the beginning of a line, so those indented headers are never recognized. Parsing still returns the full resume text, but metadata["detected_sections"] stays empty, which breaks expectations in the resume parser tests and any flow that relies on knowing which sections were found. A successful fix would allow optional leading whitespace on each line in those patterns so common sections are detected correctly and metadata lists them as intended.

**Branch name:**fix147-Resume-section-detection-fails-on-text-with-leading-whitespace 

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger