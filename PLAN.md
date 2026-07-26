## Solution plan

**Issue:**
Skill extractor fails to detect JavaScript and TypeScript
https://github.com/ascherj/pathreview/issues/148

This issue spans **four failing tests**, all in `tests/unit/test_skill_extractor.py`:
`test_javascript_detection`, `test_text_with_typescript_files`,
`test_devops_tool_detection`, `test_docker_compose_detection`.

### Understand

The root cause differs per test, but all live in `ingestion/parsers/skill_extractor.py`.
Confirmed by running `python3 -m pytest tests/unit/test_skill_extractor.py -vv -s`:

1. **JavaScript** (`test_javascript_detection`) — expected: JS detected; actual: `[]`.
   `_detect_languages` matches `re.search(r"\b(import|require)\s+", text)`, which requires
   whitespace after the keyword, so `require('fs')` never matches. The `JS_TS_KEYWORDS`
   set is defined but never scanned (Python keywords are scanned; JS/TS ones are not).
2. **TypeScript** (`test_text_with_typescript_files`) — expected: TypeScript detected;
   actual: `['Python']` (no TypeScript). TS is only detected when `.ts` appears in the
   `filename` argument; there is no content-based detection of TS syntax (`interface`,
   type annotations, `Promise<...>`, `enum`, `type X =`). The block also picks exactly one
   of JS/TS via a ternary, so both can't be reported. Note the spurious `Python`: the
   type-annotation regex matches `: string` as `str`, which the optional hardening below
   removes.
3. **Docker / Dockerfile** (`test_devops_tool_detection`) — expected: Docker detected;
   actual: `['Python']` only. `_detect_tools` matches only the literal word `"docker"`,
   which never appears in Dockerfile syntax (`FROM`, `RUN`, `EXPOSE`).
4. **Docker Compose** (`test_docker_compose_detection`) — expected: Docker detected;
   actual: `[]`. Same literal-word limitation; Compose YAML (`version:`, `services:`,
   `build:`, `ports:`) contains no "docker".

**Confirmed decisions:** when both JS and TS signals appear, report **both**; Docker
Compose folds into the **"Docker"** skill; the parser module has **no production
callers** (only the test imports it), so changing detection behavior is safe.

### Map

Single file to change: `ingestion/parsers/skill_extractor.py`
- `_detect_languages()` — JS and TS detection (issues 1 & 2)
- `_detect_tools()` — Dockerfile and Docker Compose detection (issues 3 & 4)
- `REACT_INDICATORS` / Python type-annotation regex — optional hardening

Tests validated by: `tests/unit/test_skill_extractor.py` (the only consumer).

### Plan

1. **Fix JavaScript detection** (`_detect_languages`): match `require('...')` via
   `re.search(r"\b(require|import)\s*\(", text)`, and scan the existing `JS_TS_KEYWORDS`
   (`const`, `let`, `function`, arrow `=>`, `console.log`) the same way Python keywords
   are scanned. Also detect `.js`/`.jsx` references in the text body, not just `filename`.
2. **Add content-based TypeScript detection** (`_detect_languages`): detect `.ts`/`.tsx`
   in text/filename, `interface\s+\w+`, `type\s+\w+\s*=`, `enum\s+\w+`, `Promise<`, and
   typed params `:\s*(string|number|boolean)\b`. Emit JavaScript and TypeScript as two
   independent `SkillDetection` entries when both signal sets fire.
3. **Add Dockerfile detection** (`_detect_tools`): match line-oriented keywords
   `(?im)^\s*(FROM|RUN|COPY|ADD|EXPOSE|CMD|ENTRYPOINT|WORKDIR)\b`; require ≥2 distinct
   keywords before emitting to keep confidence honest. Emit a single "Docker" skill.
4. **Add Docker Compose detection** (`_detect_tools`): detect `services:` combined with a
   Compose marker (`version:`, `build:`, `image:`, `ports:`, `container_name:`). Fold into
   the same "Docker" skill; guard against duplicate insertion.
5. **Optional hardening** (reduces noise the issue calls out): drop `.jsx`/`.tsx` from
   `REACT_INDICATORS` so a bare `.tsx` no longer reports React by itself; add `\b`
   boundaries to the Python type-annotation regex so TS `: string` stops false-matching
   Python `str`.

### Inputs & outputs

- **Input:** `extract_skills(text: str, filename: Optional[str])`.
- **Output:** `list[SkillDetection]`. After the fix, JS/TS text yields JavaScript and/or
  TypeScript entries, and Dockerfile/Compose text yields a "Docker" entry — each with
  populated `evidence` and a `confidence` in `[0, 1]`.

### Risks & unknowns

- **False positives:** generic keywords (`const`, `FROM`, `RUN`) can appear in prose;
  mitigate by requiring multiple/anchored matches before emitting a skill.
- **Reporting both JS and TS** may look redundant on pure-TS samples, but matches the
  agreed behavior and satisfies `test_mixed_language_text` (needs >1 language).
- **Optional React change** alters output for `.tsx`-only inputs; verified no other test
  depends on it.

### Edge cases

- Empty string / plain prose → return `[]` (no spurious detections).
- Dockerfile that also mentions `requirements.txt` → detect Docker (Python may also
  appear; acceptable — tests only assert "docker").
- Mixed Python + JS + TS block → detect all three.
- Case/indentation variation in Dockerfile and Compose → handle with
  `re.IGNORECASE` / multiline.

### Out-of-scope follow-up

While reproducing, a **fifth** test also fails — but it is unrelated to issue #148 and is
a bug in the *test*, not the detector. `test_database_technology_detection`
([tests/unit/test_skill_extractor.py:141](tests/unit/test_skill_extractor.py#L141)) raises
`UnboundLocalError` because it iterates over `skill_names` before defining it:

```python
skill_names = [s.name for s in skill_names]  # should iterate over `result`
```

Not fixed here to keep this change scoped to the four JS/TS/Docker issues. Track
separately (e.g. a one-line fix changing `skill_names` → `result`).

### Verification

1. `python3 -m pytest tests/unit/test_skill_extractor.py -vv -s` → all tests pass, with
   the 4 previously-failing tests now green.
2. Spot-check the issue's two examples:
   - `extract_skills('Wrote index.js using const arrow functions and async/await callbacks')`
     → includes JavaScript.
   - `extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces')`
     → includes TypeScript (and JavaScript), not only React.
3. Remove the temporary `print(...)` debug lines from the 4 tests before committing.
