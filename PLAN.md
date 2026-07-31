## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript ([#148](https://github.com/ascherj/pathreview/issues/148))

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?

- The root cause lives in `_detect_languages()` in `ingestion/parsers/skill_extractor.py` (around line 173). The JS/TS evidence check relies on a single regex, `re.search(r"\b(import|require)\s+", text)`, which only matches `import`/`require` when followed by whitespace. It never checks for `export`, `interface`, `class`, `const`, `let`, or `function`, even though a `JS_TS_KEYWORDS` set covering those exact terms is already defined earlier in the file and never used anywhere.
- Expected behavior: text that clearly describes JavaScript or TypeScript work (arrow functions, async/await, `require(...)`, `export interface`, `.tsx`/`.ts` file mentions) should produce a JavaScript or TypeScript `SkillDetection`, the same way Python, DevOps, and database content already gets picked up by their own detection paths.
- Actual behavior: `require('fs')` (no space before the parenthesis) never matches the regex, so no evidence is collected at all. Content that uses `export`/`interface`/`class` without a `.ts` filename is also invisible, since the language label itself is picked by a ternary on `.ts in filename`, not on anything in the text. Confirmed by running `pytest tests/unit/test_skill_extractor.py -v -m unit`: `test_javascript_detection` and `test_text_with_typescript_files` both fail with zero skills detected.

### Map

Which files, functions, or modules are involved?

- `ingestion/parsers/skill_extractor.py` - `_detect_languages()` is where the fix goes. This is also where the unused `JS_TS_KEYWORDS` set and `REACT_INDICATORS` set already live, so I can reuse the existing pattern the file uses for other languages instead of inventing a new one.
- `tests/unit/test_skill_extractor.py` - already has `test_javascript_detection` and `test_text_with_typescript_files`, which are the tests I need to make pass. I don't expect to need new test files, though I may add one or two more cases (e.g. `import`/`export` with no trailing space, arrow functions alone with no `require`/`import` at all) if the fix doesn't already cover them.

### Plan

What are the steps to fix this issue?

1. Reproduce and confirm scope (done - see JOURNAL.md Week 8). Only `test_javascript_detection` and `test_text_with_typescript_files` are actually about JS/TS; the other 3 failing tests in the same file are pre-existing bugs unrelated to this issue and out of scope here.
2. Widen the JS/TS evidence regex so it matches `require`/`import` regardless of what follows (`require(`, `require '...'`, `import {`, `import x from`), instead of requiring a literal space.
3. Add evidence checks for `export`, `interface`, `class`, and the other `JS_TS_KEYWORDS` terms that are currently defined but unused, so content-only samples (no filename) can still be detected the same way the issue's TypeScript example expects.
4. Reconsider the `TypeScript` vs `JavaScript` label logic so it isn't based solely on `.ts` in the filename. If `interface` or type-annotation-style TS syntax appears in the text itself, that should be enough to label it TypeScript even with no filename, mirroring how Python type annotations already contribute evidence for Python.
5. Run `pytest tests/unit/test_skill_extractor.py -v -m unit` again to confirm both target tests pass, and check that the 3 unrelated failing tests are still failing for their original, unrelated reasons (not newly broken by this change).
6. Add 1-2 additional test cases of my own (arrow function + async/await with no `require`, and `.tsx` filename with no matching text) to cover the two examples given directly in the issue body, since the existing tests use slightly different sample text than the issue's own examples.

### Inputs & outputs

- Input: arbitrary text passed to `extract_skills(text, filename=None)`, sometimes with a filename, sometimes without, as shown by the issue's two examples (plain `.js`-style code with no filename, and `.tsx`/`.ts` filenames with TypeScript-flavored text).
- Output: `_detect_languages()` populates `skills_dict` with a `JavaScript` or `TypeScript` `SkillDetection` (name, category, confidence, evidence list) whenever the text or filename gives real evidence of either language, following the same shape already used for Python.

### Risks & unknowns

Unknowns:

- How much evidence is "enough" to call something TypeScript vs JavaScript when there's no filename at all. I want to avoid making the regex so broad that plain English text mentioning words like "class" or "export" (in a non-code sense) gets falsely flagged. I'll check confidence scoring and maybe require at least two independent signals before labeling, similar to how Python already accumulates multiple evidence items before reporting.
- Whether fixing this regex could change results for the 3 unrelated failing tests. I don't expect overlap since those are about Docker/database detection, not language detection, but I'll rerun the full file, not just the two target tests, to be sure I haven't shifted anything unexpected.

Risks:

- Overly broad keyword matching could introduce false positives on non-code text (e.g. a resume that says "I exported reports as PDF" containing the word "export"). I'll keep matches anchored to code-like syntax (e.g. `export\s+(default\s+)?(class|interface|function|const)`) rather than bare keyword substrings, to avoid this.
- `JS_TS_KEYWORDS` was defined but never wired in for a reason I don't know yet; it's possible an earlier version of this code intentionally avoided it because it was too noisy. I'll test with real-sounding non-JS text as a sanity check before relying on it directly.

### Edge cases

- Text with `require`/`import` immediately followed by a parenthesis or quote and no space (e.g. `require('fs')`, `import('./thing')`), which is what the existing failing test already covers.
- Text with no filename at all that still clearly reads as TypeScript because of `interface`/`export class`/type annotations, matching the issue's second example.
- Text that mentions React (`.tsx`, `useState`) which already gets detected correctly today, I need to make sure my change doesn't accidentally duplicate or conflict with the existing `_detect_react()` logic, since a `.tsx` file is arguably both React and TypeScript.
- Plain-English text that happens to contain common-English words that overlap with JS keywords (e.g. "class," "let," "const" used outside of code), which should not falsely trigger a JavaScript/TypeScript detection.
