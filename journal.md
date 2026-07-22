## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace
 #147

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the resume_parser.py, leading indents or whitespaces are forcing new sections to be unaccounted for. Each new line is supposed to be a section but with the indents they are not detected. Once this issue is fixed the parser should be able to detect the correct resume sections even if they contain leading indents or whitespace. 

**Branch name:** fix/147-resume-section-detection-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger 