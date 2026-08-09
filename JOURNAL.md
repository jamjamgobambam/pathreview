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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sarahmsry/pathreview/commit/761d6152eac0b50556256ac6c1f9de56f65cc6f8

**Reproduction summary:**
In order to reproduce my bug I ran the test cases written for resume_parser.py and I also used other sample tests written by Claude.

**PLAN.md link:** https://github.com/sarahmsry/pathreview/blob/fix/147-resume-section-detection-error/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] N/A

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
- I've gone through the test file and understand where all of the exact issues are arrising. I still have not made any code changes. 

**Next steps:**
[What are you working on for the rest of the week?]
- I am working on rewriting the code in resume_parser.py

**Blockers:**
[Anything slowing you down? Or leave blank.]
- Not understanding the regex functionality completely in resume_parser.py

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/516

**Branch:** fix/147-resume-section-detection-error

**What you built:**
ingestion/parsers/resume_parser.py
_detect_sections: added [ \t]* after the ^ anchor so indented headers are
detected; collapsed the four patterns to two (the \n-anchored pair was
redundant under re.MULTILINE, which already matches every line start).
_strip_markdown: same fix (r"^[ \t]*#+\s+") so indented Markdown headers
(  ## Experience) get their # markers stripped.

**Tests added or updated:**
I changed test_resume_parser.py. 
Added test_detect_sections_with_leading_whitespace — asserts indented input (spaces and tabs) detects the same section set as flush input.
Added test_strip_markdown_headers_with_leading_whitespace — asserts indented Markdown headers are stripped while header text is preserved.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** Marina Moreira Tribolet


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
- N/A - no feedback for summer 2026 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---
### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
- Working with such a large codebase felt overwhelming particularly because of the fact that there were so many pre-existing issues that were outside of the scope of my own issue. It was difficult to keep track of what issues I may have caused vs what already existed, and how to avoid creating more issues that affected things outside of the scope of my issue. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
- I learned that there is a lot more to consider when altering code. I could easily fall into scope creep if I kept trying to tackle issues I created that accidentally affected a file outside of the ones I was working in. In my own projects I can easily go back and check changes I made and understand where the issue lies without altering anyones code.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
- AI was extremely helpful in breaking down confusing portions of code and helping me to understand how the files I planned to work on were related to issues outside of my scope. It was also helpful in coming up with tests to write and how to make sure my tests were only related to my change. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
- I would give myself more time for implementation. I underestimated how long it would take me to make such a minor change and I ended up having more issues than expected. I spent much longer on planning because I felt like planning extensively would prevent bugs from coming up once I made my changes but that was not the case. I also would give myself more time to deeply explore the codebase. I understood the codebase enough to make my changes, but once other bugs started arising I felt overwhelmed because I wasn't sure what type of problem I created. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
- I am proud of simply completing this PR and pushing through until the end. It was a very difficult few weeks but I was able to finish this and I learned a lot about how contributing to large codebases works. 