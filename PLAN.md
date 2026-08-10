## Solution plan

**Issue:** [#148 — Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148) (tier-1, `ingestion`)

### Understand

`SkillExtractor.extract_skills()` is meant to read source text and report the languages and
technologies it finds. For JavaScript and TypeScript it reports nothing at all.

The language detection lives in `_detect_languages()` in
`ingestion/parsers/skill_extractor.py`. There *is* a JS/TS branch in there, but it can
almost never fire:

1. Its only content signal is `re.search(r"\b(import|require)\s+", text)`. The `\s+` means
   it needs whitespace immediately after `require`, but real CommonJS is `require('fs')` —
   an opening bracket, no space. So `const fs = require('fs')` produces zero evidence.
2. Whether the result is labelled TypeScript or JavaScript is decided purely by filename:
   `lang = "TypeScript" if ".ts" in str(filename or "").lower() else "JavaScript"`.
   `extract_skills()` is often called with no filename (both failing tests do), so
   TypeScript can never be identified from the code itself.
3. The class defines a `JS_TS_KEYWORDS` set (`const`, `let`, `var`, `function`, `export`,
   `async`, …) but no method ever reads it — the most obvious content signal is unused.

**Expected:** JavaScript source → a "JavaScript" skill; TypeScript source (interfaces, type
annotations, generics) → a "TypeScript" skill, with or without a filename.
**Actual:** neither is reported. `test_javascript_detection` and
`test_text_with_typescript_files` both fail.

### Map

Files I expect to touch:

| File | Why |
|---|---|
| `ingestion/parsers/skill_extractor.py` | The fix — broaden the JS evidence and add content-based TS detection inside `_detect_languages()`, and actually use `JS_TS_KEYWORDS` |
| `tests/unit/test_skill_extractor.py` | Add regression tests alongside the two existing ones |

Code I need to understand (all in `skill_extractor.py`):
- `extract_skills()` — orchestrator; calls `_detect_languages()` first
- `_detect_languages()` — Python block, JS/TS block, then an extension map
- `JS_TS_KEYWORDS` — defined, currently unused
- `REACT_INDICATORS` / `_detect_react()` — already claims `.jsx`/`.tsx`; I must not conflict with it

### Plan

1. **Broaden the JavaScript evidence.** Fix the import regex so it matches `require('fs')`
   and `import x from 'y'` (drop the mandatory `\s+`; allow a bracket or quote to follow).
   Add content signals drawn from the existing `JS_TS_KEYWORDS` (`const`/`let`/`function`/
   `export`), plus `console.log` and arrow functions (`=>`).
2. **Add content-based TypeScript detection.** Look for TS-only markers: `interface X {`,
   `type X =`, `enum`, `implements`, generics such as `Promise<...>`, and type annotations
   (`: string` / `: number` / `: boolean`). Keep the existing `.ts` / `.tsx` filename signal.
3. **Choose the label from evidence, not just filename.** If TS markers are present report
   TypeScript; if only JS markers are present report JavaScript. Keep the existing
   confidence scaling style (`min(0.95, 0.6 + n * 0.1)`).
4. **Add regression tests** to `tests/unit/test_skill_extractor.py` covering: CommonJS
   `require()`, ES-module `import … from`, a TS interface/annotation sample with **no**
   filename, and a plain-JS sample asserting TypeScript is *not* reported.
5. **Run the suite** (`make test-unit`) and confirm the two target tests pass and nothing
   that passed before now fails.

### Inputs & outputs

- **Input:** `extract_skills(text: str, filename: Optional[str] = None)` — raw source or
  documentation text, with an optional filename.
- **Output:** the same `list[SkillDetection]`, now also containing
  `SkillDetection(name="JavaScript" | "TypeScript", category="Language", confidence=…,
  evidence=[…])` when the text warrants it.
- **Unchanged:** the return type, the confidence-sorted ordering, and every other detector
  (`_detect_frameworks`, `_detect_react`, `_detect_databases`, `_detect_tools`).

### Risks & unknowns

- **False positives on non-JS text.** `const`, `class`, `export` and `async` appear in other
  languages, so a loose keyword match could tag Java or Markdown as JavaScript. Mitigation:
  require more than one weak signal before reporting a language.
- **TypeScript vs JavaScript overlap.** Every TS file is also broadly valid JS, so I have to
  decide whether to report both or only TypeScript when TS markers exist. Unresolved — I'll
  start with "TS markers win" and let the tests tell me.
- **Pre-existing Python false positive (out of scope).** In the same method,
  `:\s*(int|str|float|bool|list|dict)` has no word boundary, so a TS annotation `: string`
  matches `str` and the TS sample also gets tagged Python; likewise `\bimport\s+\w+` fires on
  ES-module imports. I'm not fixing that under this issue, but I must confirm my change
  doesn't make it worse.
- **Scope creep.** Three other tests in the same file fail
  (`test_database_technology_detection`, `test_devops_tool_detection`,
  `test_docker_compose_detection`). Those are separate gaps and I'm deliberately leaving
  them alone so this stays a focused PR.
- **Unknown:** whether maintainers want `.jsx`/`.tsx` to imply React *and* the language.
  `_detect_react()` already claims those extensions, so I need to avoid double-reporting.

### Edge cases

- TypeScript source passed with **no filename** — the exact case the failing test exercises.
- A `.ts` / `.tsx` **filename with little recognisable content** — should still report TypeScript.
- **Plain JavaScript with no TS markers** — must report JavaScript and must *not* report TypeScript.
- **Empty or whitespace-only text** — should return no language rather than crash.
- **Mixed-language documents** — `test_mixed_language_text` feeds Python *and* JS; both
  should still be reported and that test must keep passing.
- **Prose that only mentions the word** ("we use JavaScript at work") — I'll stay conservative
  and rely on syntax markers rather than bare keyword mentions.
