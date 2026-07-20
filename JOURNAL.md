## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/147]

**Issue title:** [Resume section detection fails on text with leading whitespace
 #147]

**Tier:** [ x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[This issue affects the section-detection logic in `ingestion/parsers/resume_parser.py`, specifically the `_detect_sections()` method. The current regular expressions assume that headings such as “Education,” “Experience,” and “Skills” begin at the first character of a line. However, text extracted from PDFs often contains leading spaces or tabs, causing valid headings to be ignored and `detected_sections` to remain empty. A successful fix would update the matching logic to accept optional leading horizontal whitespace while preserving accurate section detection and avoiding new false positives.]

**Branch name:** [fix/147-Resume-section-detection-leading-whitespace]

**Setup confirmation:** [x ] App runs locally at localhost:5173

**Cohort ledger:** [x ] Issue added to cohort ledger