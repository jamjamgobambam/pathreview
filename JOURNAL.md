# Journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why I picked this issue:**
I switched to this issue after my original pick, issue #130, got closed by the professor for being based on a false premise. It turned out docker-compose.yml never actually had the LLM proxy service that issue described, so there was nothing real to fix. This time I wanted to make sure my pick was a real, reproducible bug before committing to it, and #148 fit that. The issue gives two concrete examples of text that should trigger skill detection but doesn't, so I can run those same inputs through extract_skills() myself and see the bug instead of just taking the report at face value. It's also tagged tier-1, which felt like the right move after a tier-3 issue turned into a dead end, and it's scoped to one function in the ingestion pipeline instead of spreading across a bunch of files.

**Problem summary:**
extract_skills() is supposed to detect programming languages and frameworks mentioned in text, but right now it basically can't see JavaScript or TypeScript. The issue gives two examples: text about writing index.js with arrow functions and async/await comes back with zero detected skills, and text mentioning app.tsx and types.ts with TypeScript interfaces only detects React while missing TypeScript and JavaScript entirely. Detection for Python, DevOps, and database skills works fine, so this looks like a gap specific to how the JS/TS family gets matched rather than a problem with the whole function. Four test cases in the test suite are currently failing because of this. Fixing it means extract_skills() needs to reliably pick up JavaScript and TypeScript the same way it already handles those other languages.

**Branch name:** fix/148-skill-extractor-js-ts

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction

**What I did to reproduce this:**
The repo already has a test file for this function, tests/unit/test_skill_extractor.py, so I ran it directly instead of writing new tests from scratch: `pytest tests/unit/test_skill_extractor.py -v -m unit`. That gave me 5 failing tests, not the 4 the issue mentions, so I read through each failure instead of assuming they were all the same bug. Two of them line up exactly with the issue:

- `test_javascript_detection` feeds in `const fs = require('fs');` and expects a JavaScript skill to be detected. Nothing gets detected.
- `test_text_with_typescript_files` feeds in text using `export interface User {...}` and `export class UserService {...}`, no filename. It only expects TypeScript, but nothing gets detected either.

The other 3 failures (`test_database_technology_detection`, `test_devops_tool_detection`, `test_docker_compose_detection`) are unrelated pre-existing bugs, not JS/TS detection issues, so I am not treating those as part of this issue's scope.

**What this confirms:**
I traced both real failures to `_detect_languages()` in ingestion/parsers/skill_extractor.py (around line 173). The JS/TS evidence check only runs `re.search(r"\b(import|require)\s+", text)`, which requires a space right after `require`. `require('fs')` has no space before the `(`, so it never matches. The same block never checks for `export`, `interface`, or `class`, so TypeScript-style module code with no filename is invisible too. There is also a `JS_TS_KEYWORDS` set defined earlier in the file that would cover this, but it is never actually referenced anywhere in the detection logic, so it is dead code sitting right next to the bug.

I added a comment directly above that regex in skill_extractor.py pointing at issue #148 and the two failing tests, so the exact location is documented in the code, not just in this journal.


## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I finished steps 2 through 4 from PLAN.md. In `_detect_languages()` I widened the import/require check so it also catches `require('fs')` style calls with no space before the parenthesis, added evidence checks for `export`, arrow functions, and async/await, and added a separate TypeScript-specific check (looking for `interface` and TS-style type annotations like `: string`) so the TypeScript vs JavaScript label no longer depends only on the filename. Both `test_javascript_detection` and `test_text_with_typescript_files` pass now. I also ran the full unit suite before and after my change to check for regressions, went from 53 failing to 51 failing, so exactly the 2 tests I meant to fix and nothing else broke.

**Next steps:**
I still need to add 1 or 2 of my own test cases based on the issue's exact examples (arrow function and async/await text with no require at all, and a `.tsx` filename with no matching text in the body), since the existing tests use slightly different sample text than what the issue itself gave. After that I want to commit, push, and open the PR.

**Blockers:**
Running `make check` on the whole repo still fails, but it is 180 pre-existing lint errors in files I never touched (mostly unused variables in test_tech_detector.py and similar). I checked just my file with ruff, black, and mypy directly and it passes all three on its own, so I do not think this blocks my PR, but I wanted to note it here in case it comes up in review.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/697

**Branch:** fix/148-skill-extractor-js-ts

**What you built:**
I fixed `extract_skills()` so it actually detects JavaScript and TypeScript from real code content instead of relying mostly on filenames. It now looks for `require(`, `export`, arrow functions, and async/await as JavaScript evidence, and separately checks for `interface` (including the plural "interfaces") and TypeScript-style type annotations to decide whether to label something TypeScript, instead of only checking for a `.ts` filename.

While testing, I ran the two exact examples straight from the issue body and found my first pass at the fix still missed the TypeScript one, since it was written as plain description text ("Built app.tsx and types.ts with strict TypeScript interfaces") instead of real code, with no filename passed in at all. So I added a second layer of evidence: checking for the literal words "javascript" and "typescript" in the text, and checking for `.js`/`.jsx`/`.ts`/`.tsx` mentioned inside the text itself, not just in the filename argument. I also had to tighten my own async/await check, since a bare "await" check I wrote first would have falsely flagged plain English like "I await your reply."

**Tests added or updated:**
Added 4 new tests to tests/unit/test_skill_extractor.py: `test_issue_148_javascript_description` and `test_issue_148_typescript_description` use the issue's exact wording with no filename, `test_js_ts_keywords_do_not_false_positive_on_prose` checks that ordinary English sentences with words like "class," "let," and "await" don't get flagged as code, and `test_tsx_file_detects_both_react_and_typescript` checks that a real `.tsx` component is picked up as both React and TypeScript together. The existing `test_javascript_detection` and `test_text_with_typescript_files` also now pass.

**Self-review confirmation:** [x] make check passes for the files I touched (ruff, black, mypy all clean on skill_extractor.py and my new tests; the full repo-wide `make check` still fails from unrelated pre-existing lint errors in files I never touched)  [x] make test-unit passes for the tests this issue covers (ran the full suite before and after: 53 failed/375 passed before any of my changes, 51 failed/381 passed after, so 6 more tests pass overall with zero new failures anywhere)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
As of 08/07/2026 There has been no feedback yet on my PR. 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
The hardest part of this entire pull request was not solving the bug itself, but following the practices of a industry standard PR. Throughout all my academic career, I have been used to writing code and tests, then submitting them with a single commit and a brief description. In this module, it emphasized how intricate and important the PR process is. Getting familiar with maneuvering through the Github interface, writing a detailed PR description, and following the review process was more time-consuming than I expected. I also had to learn how to write tests that accurately reflect the issue's examples, which required careful reading and understanding of the problem.

**What did you learn about working in a large codebase?**
The biggest difference between contributing to a large codebase and writing my own code is the importance of understanding the existing structure and conventions. Jumping into a large codebase practically highlighted how a small change that you are contributing on can have an impact on other parts of the system. When working on your own project, you understand the entire codebase and can make changes without worrying about any large scale issues as much due to your familiarity with the code making and decisions from scratch.

**How did AI tools help — and where did they fall short?**
AI was imperative in helping me understand the existing codebase and the problem at hand. To me, that was the main premise of this module and where AI is most effective. I prompted claude to narrow down the relevant files and functions to understand the bug and understand the existing test and any other relevant code associated with the issue. After familiarizing myself with the issue and codebase, I just followed the usual effective prompting procedures to get the AI to help me write the code and tests eventually fixing the bug. Where it may fell short was missing some of the nuances of the existing codebase and the problem at hand, which required me to read and understand the codebase myself. A few draft fixes didn't immediately work and resulted in some new problems, and I had to iterate on them to get the final solution.

**What would you do differently if you started over?**
If I were to start over, I would spend more time upfront understanding the existing codebase as a whole. To be completely transparent, I spent a lot of time understanding the specific function and test files related to the issue, but I did not spend as much time understanding the overall structure of the codebase. Not to say I did not spend enough time on that, but in a real world scenario, I would have spent more time understanding the overall structure of the codebase and how the different components interact with each other to fully immerse myself into the project. This would have helped me to understand the bigger picture and how my changes fit into it.

**What are you most proud of from this module?**
I am most proud of my ability to adapt to the PR process and the review process. That essentially was the main goal of this module. I'm proud to have had an actual practical experience of contributing to a large codebase from beginning to end. Learning how to select an issue, understanding the process of reproducing it, building a solution, writing tests, and submitting a PR for review was a very valuable experience. 
