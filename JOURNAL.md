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



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/LaurenM64/pathreview/tree/fix/147-resume-whitespace

**Reproduction summary:**
I created a test in test_resume_parser.py that had extra whitespace added in a variety of cases.  Running the tests created the specified error where the resume parser could not parse those cases and failed.  

**PLAN.md link:** https://github.com/LaurenM64/pathreview/blob/fix/147-resume-whitespace/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:** Implemented the fix for Issue #147 in `resume_parser.py`. I updated the regular expressions in both `_detect_sections()` and `_strip_markdown()` to include `[ \t]*`, allowing the parser to correctly identify headers and markdown syntax even if they are indented with spaces or tabs.
**Next steps:** Run the test suite to confirm the fix, check for linting errors, and open a pull request.
**Blockers:** None.

---

### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/690
**Branch:** `fix/147-resume-whitespace`
**What you built:** I updated the regex patterns in the resume parser to tolerate leading spaces and tabs. This ensures that sections like "Experience:" or "Education:" are still detected and properly parsed even if the text extraction includes random indentation formatting.
**Tests added or updated:** I updated `tests/unit/test_resume_parser.py` by adding `test_detect_sections_with_leading_whitespace` to reproduce the bug. My fix caused this test, and 5 other pre-existing tests in that file, to turn green.
**Self-review confirmation:** 
[x] `make check` passes (Note: Pre-existing failures exist in unrelated modules)
[x] `make test-unit` passes (Note: Pre-existing failures exist in unrelated modules)
**Draft PR feedback received from:** none



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
N/A

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
Dealing with setting up the project in the first place was difficult, as there were a lot of moving parts including figuring out how to install Docker.  Additionally, getting used to the codebase itself was tricky, although the earlier project had helped with that.  

**What did you learn about working in a large codebase?**
Getting used to someone else's syntax and code organization strategy is difficult at first.  However, using techniques from earlier projects helped to find where I need to enter the codebase and how to go between the files to get the full story.  

**How did AI tools help — and where did they fall short?**
AI assistance helped me understand specific files that I was unfamiliar with, especially ones involving databases.  It helped me to also talk through my ideas and understand where specifically my knowledge was falling short.  However, I still had to identify what files to pass into the AI, as I could not just shove the entire project into AI to determine that.  

**What would you do differently if you started over?**
Now that I have a better idea on the whole process, I would choose a different issue that was more difficult.  I would approach it with less AI guidance since I feel more confident with identifying where in the codebase and file the issue may me,  

**What are you most proud of from this module?**
Being able to go through a difficult codebase and successfully finding a bug, this is something I definitely would have struggled with earlier on.  