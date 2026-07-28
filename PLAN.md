## Solution plan

**Issue:** [Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?  

The root cause lies in `skill_extractor.py`between line 174-192. The current code for JavaScript and TypeScript filename detection
only checks for the `filename` parameter. It does not check for the `.js`, `.jsx`, `.ts`, and `.tsx` inside the text itself.
The user could be casually mentioning their skills and not providing files they have worked on and the current code would miss
all the mentions of their work. It is also missing other keyword detector listed in `JS_TS_KEYWORDS` like `const`, `let`, `var`, etc.

The expected behavior is the detector should be able to detect more JavaScript and TypeScript related keywords and also able to
detect filename extensions within the text itself rather than just relying on the user passing in the `filename` parameter. 
It should also detect Docker keywords and `Dockerfile` and `docker-compose.yml` name.

The current behavior lacks the Docker detector entirely unless the text contains the word `docker`. For JavaScript and TypeScript, 
the filename detection only works if the user passes in the files themselves, it cannot yet detect the filename mentions in the text.
For the keyword detection, it can only detects `import`, `require`, and `package.json`. But `require` can still fail since the detector
expects some whitespaces immediately after the keyword i.e. `require("fs")` would fail to be detected.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files: `ingestion/parsers/skill_extractor.py` for code and `tests/unit/test_skill_extractor.py` for tests.
Functions: 
  - Code: `extract_skills()` -> `_detect_languages()` and `extract_skills()` -> `_detect_tools()`
  - Tests: `test_javascript_detection()`, `test_text_with_typescript_files()`, `test_devops_tool_detection()`, `test_docker_compose_detection()`
Modules: `ingestion/parsers` and `tests/unit`

The code changes would mainly be in `_detect_languages()` line 174-192 and `_detect_tools()` line 267-277.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. In `_detect_languages()`, add a regex scan of the text for `.js`, `.jsx`, `.ts`, `.tsx` extensions so filename mentions in text are caught without a `filename` parameter.
2. In `_detect_languages()`, expand the JS/TS keyword check to use more of `JS_TS_KEYWORDS` — add `const`, `let`, `var`, `export`, `function` alongside `import`/`require`. Also fix the require regex from `\s+` to `\b` so `require('fs')` matches.
3. In `_detect_languages()`, add TypeScript-specific text patterns: the word `typescript`, `interface` declarations, and generic type syntax (`: string`, `Promise<`, etc.) so TypeScript can be detected from prose without a `.ts` filename.
4. In `_detect_tools()`, add Dockerfile keyword detection (`FROM`, `RUN`, `EXPOSE`, `CMD`, `ENTRYPOINT`) and docker-compose indicators (`services:`, `docker-compose`) so Docker is detected without the word "docker" appearing explicitly.
5. Run the four failing tests to confirm they pass, and verify no existing passing tests regress.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: A string of text (and an optional `filename` parameter) passed to `extract_skills()`. The text may be prose describing work experience, source code snippets, or configuration file content.

Output: A list of `SkillDetection` objects sorted by confidence. After the fix, text containing JS/TS keywords, `.js`/`.jsx`/`.ts`/`.tsx` extension mentions, TypeScript syntax, or Dockerfile/docker-compose content should produce the appropriate `SkillDetection` entries that are currently missing.

What changes: No new inputs or outputs are introduced — the function signature stays the same. Only the detection logic inside `_detect_languages()` and `_detect_tools()` changes to catch more patterns from the existing input.

### Risks & unknowns
What could go wrong? What are you still unsure about?

Risks:
- Broadening the JS keyword list (`const`, `let`, `var`) risks false positives — these words appear in plain English and other languages. A sentence like "let me explain" could trigger JavaScript detection.
- Adding Dockerfile keyword detection (`FROM`, `RUN`) carries the same risk — common English words that could appear in non-code text.

Unknowns:
- Whether the fix should require a minimum number of keyword matches (2+) before emitting a detection, to guard against false positives from common English words like `let`, `var`, `FROM`, or `RUN`. The current codebase only requires 1 match before emitting the detection.
- Whether TypeScript and JavaScript should ever be detected simultaneously from the same text, or if detecting TypeScript should suppress JavaScript.

### Edge cases
What inputs or states should your fix handle gracefully?

- Text containing `let` or `const` in plain English context (e.g. "let me explain the const approach") — should not trigger JavaScript detection.
- Text mentioning `.ts` in a non-TypeScript context (e.g. "exports.ts" or a timestamp abbreviation "10 ts ago") — should not trigger TypeScript detection.
- Text that mentions both `.tsx` and TypeScript keywords — should emit TypeScript, not JavaScript (`.tsx` is in `REACT_INDICATORS` and currently only triggers React).
- Empty string or whitespace-only input — already handled, should continue returning `[]`.
- Text with mixed JS and TS signals — should emit whichever has stronger evidence, or both if warranted.
- Dockerfile content passed as text with no `filename` — should detect Docker after the fix.
