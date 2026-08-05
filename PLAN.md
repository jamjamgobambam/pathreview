## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript (#148)
https://github.com/ascherj/pathreview/issues/148

### Understand
The root cause is in `_detect_languages()` in `ingestion/parsers/skill_extractor.py`.
JS/TS detection only checks for `.js`/`.ts` file extensions (which requires a filename
to be passed in, often not the case) and a regex `\b(import|require)\s+` that requires
whitespace immediately after the keyword. This fails on common patterns like
`require('fs')` (no space before the parenthesis) and never matches TypeScript-specific
syntax like `export interface`, `export class`, or type annotations. Separately,
`REACT_INDICATORS` includes the literal substrings `.tsx` and `.jsx`, so any text that
merely mentions a filename like `app.tsx` incorrectly triggers a "React" match instead
of a TypeScript one. Expected: JS/TS code and TypeScript-specific syntax should be
reliably detected. Actual: JS text returns no detections, and TypeScript text returns
only a false-positive "React" match.

### Map
- `ingestion/parsers/skill_extractor.py` — `_detect_languages()` method (core fix)
- `ingestion/parsers/skill_extractor.py` — `REACT_INDICATORS` set (remove/adjust `.tsx`/`.jsx` false-positive triggers)
- `tests/unit/test_skill_extractor.py` — verify fix against `test_javascript_detection`, `test_text_with_typescript_files`, and confirm no regressions in `test_react_detection`, `test_devops_tool_detection`, `test_docker_compose_detection`

### Plan
1. Add JS-specific syntax regexes to `_detect_languages()` (e.g. `const`, `let`, `function`, `=>`, `console.log`, `require(` without requiring trailing whitespace)
2. Add TypeScript-specific syntax regexes (e.g. `interface`, `: string`/`: number` type annotations, `export class`, generics like `Promise<...>`)
3. Wire in the existing but currently unused `JS_TS_KEYWORDS` set as part of this detection (or replace it with the new regexes if a cleaner approach)
4. Fix `REACT_INDICATORS` so `.tsx`/`.jsx` substrings don't cause TypeScript/JavaScript text to be misclassified as React — likely by removing these as standalone triggers, or only counting them when combined with other React-specific evidence
5. Re-run the full test suite to confirm `test_javascript_detection` and `test_text_with_typescript_files` pass without breaking `test_react_detection`, `test_devops_tool_detection`, or `test_docker_compose_detection`

### Inputs & outputs
Input: a text string (source code, resume text, or docs) and an optional filename.
Output: a list of `SkillDetection` objects, sorted by confidence, correctly including
"JavaScript" and/or "TypeScript" entries when the text contains that language's syntax.

### Risks & unknowns
- Broadening the JS/TS regexes could introduce false positives on unrelated text (e.g. the word "class" or "function" appearing in plain English) — need to balance recall vs. precision, similar to how Python's regexes are fairly syntax-specific
- Unclear why `test_devops_tool_detection` and `test_docker_compose_detection` are listed as failing in the issue — need to run them locally to confirm whether they're a separate unrelated bug or a side effect of the same detection logic
- Changing `REACT_INDICATORS` could affect existing passing tests like `test_react_detection` — needs careful regression testing

### Edge cases
- Text with both JS and TS syntax mixed together (should detect both, not just one)
- Text mentioning a `.tsx`/`.jsx` filename without any real code (should not force a React false-positive)
- Empty text input (should return an empty list, not error)
- Text with `require(...)` with no space vs. `require (...)` with a space (both should be detected)