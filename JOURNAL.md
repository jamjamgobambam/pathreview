## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/149)

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
StructuralChunker is not supposed to return an empty list for any document without a heading. It is essentially excluding the entire document from the RAG index instead of trying another strategy. A successful fix would have the chunker either return an error message, alerting the user of what is happening, or it should try another method for chunking. 

**Branch name:** fix/149-structural-chunker-silently-drops-documents

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/c365e22c1a92590de989216cae2b763a77fe7b4a

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?] 
To reproduce the issue, I used one of the included unit tests within the pathreview project. Under the tests subfolder (pathreview/tests/unit/test_structural_chunker.py) and with the virtual environment activated, I ran the command "python3 -m pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings -v", which specifically uses the test_document_with_no_headings function in the structural_chunker python file. Running the test function, it returns an AssertionError (assert 0>= 1). 

**PLAN.md link:** https://github.com/JohnPhm/pathreview/blob/fix/149-structural-chunker-silently-drops-documents/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Going into week 9, I am still confused on how to write and modify unit tests to confirm that my fixes to the structural chunker works correctly. 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far, I have been able to confirm that the issue exists and am able to reproduce the issue. This was done using the test_structural_chunker.py testing file, which resulted in the message "assert 0 >= 1" and lets us know that the functionality of structural chunker is incorrect. 

**Next steps:**
For the rest of the week, I will be working on the implementation of the issue fix as well as the documentation and reasoning behind the implementation. 

**Blockers:**
Going from planning to implementation is taking longer than I expected. Furthermore, there are many errors that occur from using make lint, more specifically, there are 77 errors. 

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1014

**Branch:** fix/149-structural-chunker-silently-drops-documents

**What you built:**
For structural_chunker.py, the fix introduced was on the content branch and the final save. I removed both gates so that the lines are always collected. Furthermore, the current_level variable was removed as it was not being used. 
For test_structural_chunker.py, the functions test_heading_path_format and test_heading_path_breadcrumb both had a boolean flag inside a loop that never got checked. This meant that both passed even if chunk() returned nothing. This was resolved by adding a trailing assertion to both of the functions. 

**Tests added or updated:**
The files that I touched include structural_chunker.py and test_structural_chunker.py. These two files are the ones that contain the actual error itself. Structural_chunker.py is the file that works as a chunker for RAG systems. The test_structural_chunker.py file works to test the functionality of each function found in the structural_chunker.py file. More specifically, the function test_document_with_no_headings() tests the implementation of the new code as it presents the chunker with a heading-less document. If the test passes, then it means that our logic and implementation was correct. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
I am still waiting for feedback of my pull request. 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
Since I did not technically receive any feedback about my PR on GitHub itself, I based my changes on the feedback that I received from the CodePath graders. The main feedback that I received about my PR was certain areas were lacking detail, such as the testing methodology and reasons why the test should be included/used. I added more detailing, explaining what the tests did and why I included/noted them in the PR. Furthermore, I also explained why I changed each file related to the issue and noted the reason why the issue occurred and why the solution worked. 

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
For me, the parts that were harder than I expected were contributing to GitHub using the git commands in the terminal and attempting to fix the errors found when using 'make check'. I ran into multiple issues trying to connect my local machine to my GitHub as it kept asking me for reauthentication since my token expired. I had to generate a new one and I used Claude to guide me through the process as this was the first time I have encountered this error. On the other hand, I used the command 'make check' and there were 77 errors that resulted from the command. For a while, I thought that I needed to correct these errors before committing and pushing to GitHub but in retrospect, I realized this too far down the line. My section of interest did not come into contact with the majority of the errors so I did not have to fix the errors myself. Only the errors that concerned the area around my issue would need to be fixed. This made it difficult at the beginning but I realized that it was unncessary to fix.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that building my own project and contributing to someone else's production code requires you to follow the guidelines that are established so that everyone contributing to that codebase is able to easily understand the changes. If there are coding conventions and contribution guidelines laid out, then it is best if I follow it to not risk my contributions being rejected. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
For this module, I used Claude to assist me whenever I encountered an error. There were times when the token for authentication expired and I had to browse through the GitHub settings to generate a new token and reauthenticate it. Claude helped walked me through this process and explain what and why it happened. The areas where Claude fell short include suggestions for the first implementation of structural_chunker.py. I had to read through the structural_chunker.py file itself and provided extra context to Claude so that it can provide further fixes to the new implementation. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
If I started over, I would focus more on the process of iteratively fixing and committing each implementation. During the course of this module and the previous module, I was able to apply the correct implementation to alleviate the issue but I kept forgetting to regularly commit my changes and documenting why I included each change. This made it difficult as each time I took a break and came back, I felt momentarily lost as I had nothing to refer to in terms of my progress. 

**What are you most proud of from this module?**
The thing that I am most proud of from this module would be becoming proficient in using Git to stage and commit code directly from the VSCode terminal while also maintaining the standard of the commits. 