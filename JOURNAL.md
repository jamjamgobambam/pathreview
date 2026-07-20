## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser detects section headers (like "Education" or "Skills") using
regex patterns that only match when a header starts at the very beginning of a
line, with no leading whitespace. PDF-extracted resume text frequently has
indented lines, so real-world input causes the parser to find zero sections
even when they're clearly present. This affects `_detect_sections()` in
`ingestion/parsers/resume_parser.py`, and breaks downstream logic that depends
on knowing which sections a resume contains. A fix should let the header
patterns match regardless of leading whitespace/indentation on each line.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger