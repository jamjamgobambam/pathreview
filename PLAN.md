## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript (#148)
https://github.com/ascherj/pathreview/issues/148

### Understand
`extract_skills()` in `ingestion/parsers/skill_extractor.py` is supposed to detect
programming languages, frameworks, tools, and databases from resume/repo text. Python,
DevOps, and database detection all work correctly, but JavaScript and TypeScript
detection is effectively broken. Running the issue's own examples confirms this:
`extract_skills('Wrote index.js using const arrow functions and async/await callbacks')`
returns `[]` instead of `JavaScript`, and
`extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces')` returns
only `['React']` instead of also including `TypeScript`. Expected behavior: real JS/TS
syntax and plain-text mentions of JavaScript/TypeScript (filenames, extensions, the words
themselves) should be detected as evidence, the same way Python detection already checks
for `import`, `def`, and type annotations directly in the text. Actual behavior: JS/TS
detection is almost entirely gated on a `filename` argument that's frequently not
provided, and the one text-based check that exists is too narrow to catch common syntax.

### Map
- `ingestion/parsers/skill_extractor.py` — contains `_detect_languages()`, the method
  directly responsible for the bug, plus `JS_TS_KEYWORDS`, a class attribute that's
  defined but never referenced anywhere in the file
- `tests/unit/test_skill_extractor.py` — existing test suite; contains
  `test_javascript_detection`, `test_text_with_typescript_files`,
  `test_devops_tool_detection`, and `test_docker_compose_detection`, which the issue
  lists as currently failing
- `_detect_react()` and `REACT_INDICATORS` — not buggy themselves, but relevant context
  since `.tsx` being a literal React indicator is why TypeScript examples currently
  return `React` at all

### Plan
1. Reproduce both of the issue's examples locally against `extract_skills()` and confirm
   they match the "observed" output in the issue exactly.
2. Read `_detect_languages()` line by line to find the actual root cause rather than
   assuming from the issue description alone.
3. Rewrite the JavaScript evidence checks to look at real syntax in the text itself
   (import/require — including `require('fs')` with no space, `export` statements,
   arrow function syntax, `async`/`await`), plus a literal "javascript" / `.js`/`.jsx`
   mention check, since the issue's own examples describe files in plain English rather
   than pasting real code.
4. Add a fully independent TypeScript evidence check (interface declarations, type
   annotations, literal "typescript" mention, `.ts`/`.tsx` mentioned in text) so
   TypeScript no longer depends solely on a `.ts` filename, and so a `.tsx` file can
   correctly produce both JavaScript and TypeScript rather than one or the other.
5. Add tests: the issue's two exact examples, a negative test confirming plain English
   sentences containing words like "class" or "let" are not falsely flagged as code, and
   a realistic `.tsx` file test expecting both React and TypeScript.
6. Run `make test-unit`, `make lint`, and `make typecheck` scoped to the touched file and
   confirm the four previously-failing tests listed in the issue now pass.

### Inputs & outputs
Input: current `ingestion/parsers/skill_extractor.py`, the issue's two repro examples,
the existing test file's conventions. Output: an updated `_detect_languages()` method
with independent JavaScript and TypeScript evidence checks, four new/updated tests in
`tests/unit/test_skill_extractor.py`, and a PR closing # 148.

### Risks & unknowns
- Broadening detection too aggressively (e.g. matching on bare keyword membership like
  "does `let` or `class` appear anywhere") risks false positives on plain English text —
  need to keep every check structural (regex requiring real syntax shape), not
  bag-of-words matching.
- `JS_TS_KEYWORDS` exists as unused class data; unclear if it was meant to be used
  differently (e.g. a scoring/weighting approach) than what I'm implementing — proceeding
  with explicit regex checks since that matches the existing pattern used for Python
  detection in the same method.
- The pre-existing Python import check (`re.search(r"\bimport\s+\w+", text)`) will also
  match JS `import ... from` statements — a pre-existing false positive unrelated to
  # 148 that I'm flagging for reviewers rather than fixing, to keep this PR scoped.

### Edge cases
- A `.tsx` file that is valid JS and also has TS-specific syntax (interfaces, type
  annotations) should detect both JavaScript and TypeScript, not just one.
- Plain English sentences containing JS/TS keywords as ordinary words (e.g. "let's go to
  class") should not trigger any language detection.
- Text with no filename at all (as in both of the issue's repro examples) must still be
  detectable from syntax/literal-word evidence alone.
