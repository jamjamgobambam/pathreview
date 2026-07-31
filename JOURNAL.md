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
