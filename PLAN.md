## Solution plan

**Issue:** [Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148)

### Understand
`_detect_languages()` in `ingestion/parsers/skill_extractor.py` only detects
JS/TS through two checks: the `filename` argument's extension (`.js`/`.ts`),
or the regex `\b(import|require)\s+` against the text. Expected behavior:
JS/TS should be detected from plain code content the same way Python is
(via keyword/pattern matching, no filename required). Actual behavior:
`extract_skills()` returns `[]` for JS text using `const`/`async`/`require('fs')`
(no space after `require`, so the regex misses it), and returns only
`['React']` for TypeScript text (`.tsx` mentions trigger the React detector's
substring match, but nothing detects TypeScript itself). The class already
defines a `JS_TS_KEYWORDS` set with the right keywords — it's just never
referenced in `_detect_languages()`. Separately, `_detect_tools()` only
matches the literal word "docker," so Dockerfile syntax (`FROM`, `RUN`,
`EXPOSE`) and docker-compose YAML (`services:`, `ports:`) go undetected —
same root pattern (substring matching too narrow), different method.

### Map
- `ingestion/parsers/skill_extractor.py` — `_detect_languages()` (JS/TS logic),
  `_detect_tools()` (Docker/Compose logic) — both need new pattern matching
- `tests/unit/test_skill_extractor.py` — the 4 failing tests already define
  target behavior; may add 1-2 edge-case tests of my own

### Plan
1. Add JS/TS keyword-based detection in `_detect_languages()` using the
   existing (currently unused) `JS_TS_KEYWORDS` set, following the same
   evidence-list pattern already used for Python.
2. Add TypeScript-specific signals (`export interface`, `export class`,
   `: Promise<`) so TypeScript is labeled correctly, not just detected as
   generic JavaScript or mislabeled as React.
3. Add Dockerfile syntax detection to `_detect_tools()` (`FROM `, `RUN `,
   `EXPOSE `, `COPY ` at line starts).
4. Add docker-compose syntax detection (`services:` combined with `ports:`
   or `build:`).
5. Run `make test-unit`, confirm all 4 target tests pass and the 13
   currently-passing tests still pass.

### Inputs & outputs
**Input:** raw text (source code, resume, README) and an optional `filename`
string, passed to `extract_skills(text, filename)`.
**Output:** a list of `SkillDetection` objects (`name`, `category`,
`confidence`, `evidence`). My fix changes which skills get added to that
list and what evidence they carry — it doesn't change the function
signature or the `SkillDetection` shape.

### Risks & unknowns
- Keywords like `class`, `async`, `import` also appear in Python — my JS/TS
  matching needs to avoid false-positiving on Python-only text. Plan to
  require multiple distinct keyword matches before flagging, not just one.
- `_detect_react()`'s existing `.tsx` substring match must keep working
  alongside my new TypeScript detection — both should fire on the same text,
  not compete.
- Dockerfile keywords (`FROM`, `RUN`) are common English words; need
  reasonably specific patterns (e.g., `FROM` at line start followed by an
  image reference) to avoid false positives in unrelated text.
- Confidence scores must follow the existing formula
  (`min(0.95, 0.6 + len(evidence) * 0.1)`) for consistency with Python
  detection in the same file.

### Edge cases
- Text with both JS and Python content mixed together (should detect both,
  not just one)
- Text mentioning `.tsx` without any React-specific code (should still
  detect TypeScript correctly, and React only if real React indicators exist)
- Empty text / plain English with no code (should return `[]`, not error)
- Dockerfile snippets with lowercase instructions (`from`, `run`) — should
  detection be case-insensitive?
- `test_database_technology_detection`'s pre-existing `UnboundLocalError`
  (typo in the test file, unrelated to this issue) — explicitly out of scope