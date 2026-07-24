# Plan — Issue #148: Skill extractor fails to detect JavaScript and TypeScript

## Root cause

`_detect_languages()` in `ingestion/parsers/skill_extractor.py` only detects JS/TS
through two checks: the `filename` argument's extension (`.js`/`.ts`), or the
regex `\b(import|require)\s+` against the text. This misses common real-world
cases:

- `require('fs')` — no space between `require` and `(`, so `\brequire\s+` doesn't match
- `export interface`, `export class` — "export" is never checked at all
- Plain code with `const`, `let`, `function`, `async/await` but no `import`/`require`

Notably, the class already defines a `JS_TS_KEYWORDS` set with exactly the
right keywords (`const`, `let`, `var`, `function`, `class`, `async`, `await`,
`export`, `import`, `require`) — it's just never referenced in
`_detect_languages()`. This is the main gap to close.

Separately, `_detect_tools()` only detects Docker/Compose via the literal
substring `"docker"` in the text. Dockerfile syntax (`FROM`, `RUN`, `EXPOSE`)
and docker-compose YAML syntax (`version:`, `services:`, `ports:`) never
contain that literal word, so both go undetected. Same root pattern as the
JS/TS bug: keyword/substring matching too narrow to catch real syntax.

## Files to change

- `ingestion/parsers/skill_extractor.py` — the only file with logic changes
- `tests/unit/test_skill_extractor.py` — no new tests needed (the 4 failing
  tests already specify the target behavior), but I may add 1-2 additional
  edge-case tests

## Sub-tasks, in order

1. **Fix JS/TS keyword detection** in `_detect_languages()`: use the existing
   `JS_TS_KEYWORDS` set to scan the text for word-boundary matches (similar
   style to how Python detection already checks for `def`/`import` via regex),
   in addition to the existing filename/import/require checks. This fixes
   `test_javascript_detection`.
2. **Fix TypeScript-specific detection**: ensure `export interface`/`export
   class` patterns are recognized, and that the language label becomes
   "TypeScript" rather than generic "JavaScript" when TS-specific syntax
   (`interface`, `: Promise<`, etc.) is present, not just when the filename
   ends in `.ts`. This fixes `test_text_with_typescript_files`.
3. **Add Dockerfile syntax detection** to `_detect_tools()`: check for
   Dockerfile instruction keywords (`FROM `, `RUN `, `EXPOSE `, `COPY `) at
   the start of lines, not just the literal word "docker". Fixes
   `test_devops_tool_detection`.
4. **Add docker-compose syntax detection**: check for compose-specific YAML
   structure (`services:` combined with `ports:` or `build:`), not just the
   literal word "docker". Fixes `test_docker_compose_detection`.
5. **Run full test suite** (`make test-unit`) and confirm:
   - All 4 previously-failing tests now pass
   - None of the 13 previously-passing tests break
   - (`test_database_technology_detection`'s pre-existing `UnboundLocalError`
     typo is left alone — out of scope for this issue)

## Risks / edge cases

- **Over-matching**: keywords like `class`, `import`, `async` also appear in
  Python and other languages. Need to make sure JS/TS keyword matching
  doesn't cause false positives on Python-only text (e.g., Python also uses
  `class` and `async`). Mitigation: require at least 2 distinct JS/TS
  keyword matches before flagging, similar to how confidence scales with
  evidence count elsewhere in the file, and rely on the union of signals
  rather than any single keyword.
- **React vs. TypeScript conflation**: `_detect_react()` currently treats
  any `.tsx` mention as React evidence. Need to make sure fixing TypeScript
  detection doesn't remove the (valid) React detection for `.tsx` files —
  both should be detectable from the same text.
- **Confidence scoring consistency**: any new evidence list must follow the
  existing pattern (`min(0.95, 0.6 + len(evidence) * 0.1)`) rather than
  inventing a new scoring scheme, to stay consistent with Python detection
  in the same method.
- **Docker false positives**: Dockerfile-style keywords like `FROM`, `RUN`
  are common English words / could appear in unrelated contexts (e.g., "RUN
  the tests"). Need reasonably specific patterns (e.g., `FROM` at line start
  followed by an image reference) to avoid false positives.

## Out of scope

- `test_database_technology_detection`'s `UnboundLocalError` (pre-existing
  typo in the test file itself, unrelated to this issue)
- Any other language/framework detection logic not touched by the 4 failing
  tests