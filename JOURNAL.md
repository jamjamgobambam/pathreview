## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The function extract_skills() isn't detecting text that describes JavaScript work. It also is returning 'React' for text that specifically mentions TypeScript. Similarly, it is returning "React' for text that contains file endings such as .tsx or .ts, which should indicate a TypeScript file. The issue appears to affect the SkillExtractor component in the ingestion pipeline. A successful fix would allow the SkillExtractor to correctly identify JavaScript and TypeScript while not affecting the existing skill detection behavior for other technologies.

**Selection notes**
I chose this issue because it has a clearly defined problem, is reproducible, and has existing unit tests that can be used to verify a solution. The scope appears to be manageable, as the issue appears to be limited to the SkillExtractor component. My plan is to identify why JavaScript and TypeScript are not being detected, create a targeted fix, and verify that the existing tests pass without introducing side effects in other skill detection logic.

**Branch name:** fix/148-js-ts-skill-detection

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/OzzyT26/pathreview/commit/40488ff41e7c9b951eb2d3343933c178faa548b5

**Reproduction summary:**
I reproduced issue number 148 by running the existing skill extractor unit tests and the examples from the GitHub issue description. To run the SkillExtractor tests, I ran pytest tests/unit/test_skill_extractor.py -v. I also ran the example text from the GitHub issue description using SkillExtractor.extract_skills(). The JavaScript example returned no detected skills, and the TypeScript example detected React but did not detect TypeScript or JavaScript. The existing test_javascript_detection and test_text_with_typescript_files tests also failed for the same missing detections.

**PLAN.md link:** https://github.com/OzzyT26/pathreview/commit/6c34856

**Walkthrough video (recommended):**

**Blockers or open questions:**
There are many potential things that could cause these issues. I still need to determine whether the failure is caused by missing language patterns, incorrect filename extension handling, etc. The issue could potentially be caused by other less obvious areas as well, such as normalization, confidenct thresholds, etc. 

I'm still investigating which JavaScript and TypeScript language features the extractor is intended to recognize. The existing tests rely on code snippets rather than plain-language descriptions, so I need to trace how SkillExtractor detects language-specific syntax before implementing a fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have researched the differences between TypeScript and JavaScript in order to better understand their distinguishing deatures. I have compared the issue description from GitHub with the existing failing tests in order to understand which tests are elevant, and to better understand the scope of the full issue. I traced inputs through skill_extractor.py in order to identify why detections were failing. I have implemented logic changes that achieve the following:

- The SkillDetector can now recognize .js, .ts, and .tsx filenames in input text.
- The SkillDetector can now recognize the literal word TypeScript in input text.
-The SkillDetector now recognizes common JavaScript and TypeScript syntax.

I also implemented a test for each logic change that I made in skill_extractor.py.  The tests are as follows:
- test_javascript_detection_from_filename_in_text verifies that JavaScript is detected when a .js filename is mentioned directly in the input text.
- test_typescript_detection_from_ts_filename_in_text verifies that TypeScript is detected when a .ts filename is mentioned directly in the input text.
- test_typescript_detection_from_tsx_filename_in_text verifies that a .tsx filename is recognized as TypeScript evidence, while preserving the existing React detection.
- test_typescript_detection_from_language_name_in_text verifies that TypeScript is detected when the literal language name appears in the input text.

I also verified that the existing test_javascript_detection and test_text_with_typescript_files tests now pass. The complete test_skill_extractor.py file currently has 19 passing tests and three pre-existing failures related to database, Docker, and Docker Compose detection.

**Next steps:**
Now that my implementation is complete, my next step is to open my pull request, request peer feedback, and submit for review. I'll also update JOURNAL.md.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/836

**Branch:** `fix/148-js-ts-skill-detection`

**What you built:**
I updated SkillExtractor so that JavaScript and TypeScript are detected when evidence appears directly in the input text instead of relying only on the optional filename parameter. The detector now recognizes .js, .ts, and .tsx filenames in text, the literal word TypeScript, and additional JavaScript and TypeScript syntax while preserving the existing detection behavior for other languages and frameworks.

**Tests added or updated:**
I updated tests/unit/test_skill_extractor.py by adding targeted regression tests for JavaScript detection from .js filenames in text, TypeScript detection from .ts and .tsx filenames in text, and TypeScript detection from the literal word TypeScript. I also reran the full test_skill_extractor.py test suite to verify that the related JavaScript and TypeScript tests now pass.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

make check and make test-unit report pre-existing failures outside the scope of Issue #148. I verified my changes by running the focused checks for skill_extractor.py and the complete tests/unit/test_skill_extractor.py test suite.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
When I first read the issue description and saw that it listed related tests in the test_skill_extractor test suite, I thought this would be an easy way to reproduce the issue and test my fixes. However, I found that the tests in test_skill_extractor were related, but didn't cover the exact issues described in the issue. I ended up writing my own tests to reproduce those cases. Committing my work also ended up being much harder than I expected. When I tried to commit, mypy would sometimes block my commits because of type-checking errors that were unrelated to the part of the codebase I was working on.

**What did you learn about working in a large codebase?**
I learned that I have to understand a project's conventions and follow them. I hadn't thought much about that before. In group projects that I completed in school, everyone did their own part, mostly using their own conventions, and at the end we put the pieces together. Here, the project was already built and conventions were established, so part of my work was learning and following the project's existing style and development conventions. I also found that the codebase was easier to navigate than I thought it would be. When I first opened it, because we had already learned about RAG pipelines, it was easy for me to figure out that skill_extractor.py would likely be in the ingestion folder.

**How did AI tools help — and where did they fall short?**
I found AI tools extremely helpful for stress-testing my ideas. I wanted to debug the issue myself, so I instructed my AI assistant not to generate the answer, but instead to collaborate with me and help me refine my ideas. There were several times when I disagreed with the AI assistant, and after I explained my reasoning, it agreed that my approach was reasonable.

For example, I was writing a test for TypeScript detection in SkillExtractor. The goal was for SkillExtractor to recognize TypeScript filename endings in the input text. The AI assistant suggested a test sentence that was full of TypeScript syntax and also included a .ts filename. I pointed out that if the text contained a lot of TypeScript syntax, it would be impossible to tell whether my new .ts filename detection was actually working or whether another part of the TypeScript detection logic was responsible for the result. I was somewhat surprised when the AI assistant agreed with my reasoning and said that the more isolated test was a better approach. This reinforced for me that AI suggestions still need to be evaluated rather than accepted automatically.

**What would you do differently if you started over?**
When I read the issue description and saw that it listed related failing tests, I assumed those tests would directly recreate the issue. Later, after reading the test_skill_extractor file more carefully, I found that this was not the case. It wasn't a major problem because I was able to create my own tests, but in the future I would read the relevant test files in more detail before selecting an issue to make sure I understand exactly what is already covered.

Also, for this particular assignment, I initially found it difficult to tell which parts of the planning process were supposed to be completed before reading the code and which were supposed to be completed afterward. This led to me spending a lot of time trying to come up with a plan without looking at the implementation. I eventually realized that I could examine the code, so I deleted my original draft and rewrote my plan after reading it. If I were starting over, I would read the relevant code much earlier in the process.

Regarding my implementation, while exploring skill_extractor.py, I found sets at the top of the file (PYTHON_KEYWORDS, JS_TS_KEYWORDS, etc.) that list keywords for different programming languages. However, these sets were not used by the original implementation. I chose not to refactor the detection logic to use these sets because I felt that would go beyond the scope of the issue I selected. However, using those existing sets could potentially improve other parts of the skill detection logic. If I had more time, I would investigate whether the detector should be refactored to use them.

**What are you most proud of from this module?**
I am most proud of opening my first PR and learning the workflow for making an open-source contribution. The issue itself wasn't too difficult to debug, but I enjoyed going through the entire process step by step: creating tests to reproduce the issue, developing a plan, implementing the fix, testing it, and making sure I didn't introduce regressions related to my changes. I was also initially intimidated by the idea of navigating a large and unfamiliar codebase, but I found it much easier to understand and work with than I expected.