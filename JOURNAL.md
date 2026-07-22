## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** ✅ Tier 1  

**Problem summary:** The issue happens because _detect_sections anchors header regular expressions to the start of a line (^ or \n), failing to account for whitespace. Because PDF extraction frequently introduces leading spaces or tabs before section headers, the rigid regex patterns miss them entirely and return an empty detected_sections list. To fix this, updating the regex patterns in resume_parser.py to permit optional leading whitespace (^\s* and \n\s*) will allow the parser to handle indented text gracefully. Ultimately, a successful fix will reliably detect section headers regardless of leading indentation and resolve the failing unit tests in tests/unit/test_resume_parser.py.

**Branch name:** fix/resume-section-leading-whitespace

**Setup confirmation:**  ✅ App runs locally at localhost:5173

**Cohort ledger:**  ✅ Issue added to cohort ledger