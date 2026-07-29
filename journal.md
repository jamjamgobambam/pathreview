## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/147)]

**Issue title:** [Resume section detection fails on text with leading whitespace]

**Tier:** [✓] Tier 1  [2173 ] Tier 2  [ ] Tier 3

**Problem summary:**

The current issue is that the section header in the pdf has a special character associated with it.
The parsing function uses the text extraction which preserves such special characters.
Due to this, the section may not be read properly or be read as blank.
Currently, check for such special character is missing and a successful fix would enable 
cleaner parsing of each section in the pdfs.
This bug can be spoted in the ingestion folder, in the resume_parser.py file.

**Branch name:** [fix/146-whitespace-detection]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger
