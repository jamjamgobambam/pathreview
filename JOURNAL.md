## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147
**Issue title:** Resume section detection fails on text with leading whitespace
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:** The ingestion pipeline currently fails to correctly identify resume sections if the text contains leading whitespace before the headers. This bug prevents those specific resumes from being properly chunked, analyzed, and scored by the RAG system. A successful fix will likely involve stripping whitespace during the parsing step so the system can reliably recognize headers regardless of minor formatting quirks.

**Is this right for me reasoning:** 
[x]I can explain the problem and the expected behavior in 2–3 sentences without reading the issue. (summary above)
[x]I've located the relevant files and confirmed they exist in the codebase. 
resume_parser.py within the parsers folder.

[x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after. 
Before: empty text in detected_sections outputs.  After: should be full with the content in the header.


[x]The tier is a realistic match for where I am right now (tier 1)

[x] I've found and read the specific code the issue references (not just the file — the function or section). _detect_sections() in resume_parser.py specifically lines 122/123: 
"# Remove extra whitespace
text = re.sub(r"\n{3,}", "\n\n", text)"


[x]I've read enough surrounding context that I can write a rough plan for the fix without looking anything up. 
I will need to understand the current logic for removing the whitespace and find what is causing the bug. It is likely within lines 122/123 as those are the lines handling whitespace removal but I will investigate the other calls to "text" as well. 

[x]I've found the test file for my module and read at least one test end-to-end.

[x]I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

[x]I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
[x]This issue has no open blockers or dependencies on other unresolved issues.

**Branch name:** fix/147-resume-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger