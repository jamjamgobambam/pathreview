## Solution plan

**Issue:** #148 — Skill extractor fails to detect JavaScript and TypeScript
https://github.com/ascherj/pathreview/issues/148

### Understand

**Root cause:** `_detect_languages()` in `ingestion/parsers/skill_extractor.py` only checks the optional `filename` parameter for `.js`/`.ts` extensions. It never scans the text body itself. So when text like `Wrote index.js using const arrow functions and async/await callbacks` is passed without a `filename` argument, the JS/TS detection block finds zero evidence and returns nothing.

Additionally:

- The regex `re.search(r"\b(import|require)\s+", text)` requires a space after `require` — so `require('fs')` does not match because the opening paren follows immediately.
- The literal words `"JavaScript"` and `"TypeScript"` are never checked.
- Docker detection (`_detect_tools`) matches the literal string `"docker"`, which does not appear in Dockerfile content (`FROM`, `RUN`, `EXPOSE`) or docker-compose files (`version:`, `services:`, `build:`).

**Expected behavior:** Given text describing JavaScript/TypeScript work (with in-text file extensions, keywords, or the language name), the extractor returns `SkillDetection` entries for JavaScript and/or TypeScript. Given Dockerfile or docker-compose content, it returns `Docker`.

**Actual behavior:** JS text returns `[]`; TS text returns only `['React']` (incidental match via `.tsx` in the React indicator list). Dockerfile content returns no Docker skill.

### Map

Files to touch:

| File                                   | Role                                                                  |
| -------------------------------------- | --------------------------------------------------------------------- |
| `ingestion/parsers/skill_extractor.py` | Main logic — `_detect_languages()` and `_detect_tools()` need changes |
| `tests/unit/test_skill_extractor.py`   | Existing tests that must continue to pass after the fix               |
| `tests/unit/test_local.py`             | Manual reproduction script (already exists, no changes needed)        |

### Plan

1. **Enhance JS/TS in-text file extension detection** — Scan the text body for `.js`, `.jsx`, `.ts`, `.tsx` extension mentions (e.g., `index.js`, `app.tsx`). Use a regex like `r'\w+\.(js|jsx|ts|tsx)\b'` to catch these without false-matching on plain words ending in `.js`.

2. **Add language name detection** — Check if the text contains the literal words `"javascript"` or `"typescript"` (case-insensitive).

3. **Fix `require` pattern** — Change the regex from `r"\b(import|require)\s+"` to `r"\b(import|require)\s*\(?"` so `require('fs')` without a trailing space still matches.

4. **Add JS/TS keyword detection** — Use the existing `JS_TS_KEYWORDS` set (minus overlapping Python keywords like `import`, `async`, `await`, `class`) to look for JS-specific keywords such as `const`, `let`, `var`, `export`, `function`. A threshold of ≥ 2 unique keyword matches should trigger JS/TS detection.

5. **Enhance Docker detection** — In `_detect_tools()`, add Dockerfile-specific patterns: match `FROM`, `RUN`, `CMD`, `EXPOSE`, `ENTRYPOINT` at the start of lines (Dockerfile), and `version:`, `services:`, `build:`, `ports:` at the start of lines (docker-compose). If any of these appear, add a Docker skill entry.

6. **Update evidence strings** — Each new detection path should add a descriptive evidence string so the returned `SkillDetection` objects explain _why_ the skill was detected.

7. **Run existing tests** — Verify `test_javascript_detection`, `test_text_with_typescript_files`, `test_devops_tool_detection`, `test_docker_compose_detection` pass, and no regressions on Python/database tests.

### Inputs & outputs

**Input:** A string `text` (code snippet or natural-language description) and an optional `filename` string.

**Output:** A list of `SkillDetection` objects, each with:

- `name` — e.g. `"JavaScript"`, `"TypeScript"`, `"Docker"`
- `category` — `"Language"` or `"Tool"`
- `confidence` — float 0.0–1.0
- `evidence` — list of human-readable strings explaining the match

After the fix, the following inputs produce the expected outputs:

| Input                                                                  | Expected skills   |
| ---------------------------------------------------------------------- | ----------------- |
| `Wrote index.js using const arrow functions and async/await callbacks` | JavaScript        |
| `Built app.tsx and types.ts with strict TypeScript interfaces`         | TypeScript, React |
| `const fs = require('fs');`                                            | JavaScript        |
| `export interface User { id: string; }`                                | TypeScript        |
| Dockerfile content (`FROM python:3.9 ...`)                             | Docker            |
| docker-compose content (`version: '3.8' services: ...`)                | Docker            |

### Risks & unknowns

- **Overlapping keywords between Python and JS/TS:** Both languages use `import`, `async`, `await`, `class`. Using these as JS/TS evidence would cause false positives on Python code. Mitigation: exclude overlapping keywords from JS/TS keyword detection, and require a higher threshold (e.g., ≥ 2 unique JS-only keywords) before declaring JS/TS.
- **False positives on `.js`/`.ts` in text:** A sentence like "I need to do it ASAP.js" could match. Mitigation: require the extension to follow a word character (e.g., `\w+\.(js|ts)`) and not be preceded by a space-only context that looks like a URL.
- **Dockerfile vs docker-compose ambiguity:** Both should produce `Docker` as the skill name. The evidence strings should distinguish so developers know which pattern matched.

### Edge cases

- **Empty text:** Should return `[]` without errors (already handled).
- **Plain English text with no code:** Should return `[]` (already handled).
- **Text containing both Python and JS/TS:** Should detect both languages. Example: `test_mixed_language_text` in the test suite.
- **`.ipynb` filenames:** Should still detect Python (already works via extension).
- **`require('fs')` vs `require('fs')` with space:** Both should match after the regex fix.
- **Dockerfile with lowercase `from`:** Should match case-insensitively (e.g., `FROM`, `from`, `From`).
- **docker-compose with indented keys:** `services:` may be at column 0 or indented. Should match at any position.
- **Text with "JavaScript" or "TypeScript" as standalone words:** Should detect even without code snippets.
