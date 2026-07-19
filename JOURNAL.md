## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/147#issuecomment-4975799593)]

**Issue title:** [Resume section detection fails on text with leading whitespace]

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
[In resume_parser.py, the _detect_sections() function relies on regex patterns that require section headers to begin at the very start of a line, with nothing preceding them. This assumption fails for text extracted from PDFs, since PDF-to-text extraction frequently retains leading whitespace (spaces or tabs) from the original document layout, so headers like "Experience" or "Education" end up indented rather than flush-left. As a result, none of the section patterns match, and detected_sections returns empty even for resumes that clearly contain well-formed sections. A successful fix would make the header-matching logic tolerant of leading whitespace — either by adjusting the regex patterns or normalizing each line before matching — so that section detection works reliably regardless of whether the source text came from a PDF or another format.]

**Branch name:** [fix/147-resume-parsing-error]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
