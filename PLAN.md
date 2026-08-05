## Solution plan

**Issue:** Skill extractor fails to detect JavaScript and TypeScript — https://github.com/ascherj/pathreview/issues/148

### Understand

The skill extractor is supposed to read source text and report which
languages, frameworks, and tools appear in it. Its JS/TS and Docker detection
is too shallow, so clearly JS/TS/Docker content is missed.

Root causes (all in `ingestion/parsers/skill_extractor.py`):

1. **JS import/require regex requires whitespace.** `_detect_languages()` uses
   `re.search(r"\b(import|require)\s+", text)`. A real CommonJS call like
   `require('fs')` has a `(` immediately after `require` (no space), so it never
   matches. JS files that use `require(...)`, `export`, `const`, arrow
   functions, or `async` — but no `import ` / `require ` with a trailing space —
   are not detected at all.
2. **TypeScript is only labeled from a `.ts` filename.** The language label is
   `"TypeScript" if ".ts" in filename else "JavaScript"`. TS-only syntax
   (`interface`, typed declarations like `id: string`, `: Promise<User>`) in
   raw text with no filename is never recognized as TypeScript.
3. **Tool detection is a bare substring match on the tool name.** `_detect_tools()`
   only flags Docker when the literal string `"docker"` is present. Dockerfile
   content (`FROM` / `RUN` / `EXPOSE`) and docker-compose YAML
   (`version:` / `services:` / `ports:`) contain no `"docker"` substring, so
   they go undetected.

**Expected vs. actual**

| Input | Expected | Actual |
|---|---|---|
| `const fs = require('fs')` | JavaScript | (nothing) |
| `export interface User { id: string }` | TypeScript | (nothing) |
| `FROM python:3.9 / RUN ... / EXPOSE 8000` | Docker | (nothing) |
| docker-compose YAML (`services:`, `ports:`) | Docker | (nothing) |

### Map

- **`ingestion/parsers/skill_extractor.py`** — the only source file to change.
  - `_detect_languages()` — extend JS/TS detection to be content-based (fix
    root causes 1 and 2). Add a `JS_TS_KEYWORDS` / regex-based signal set and a
    TypeScript-specific signal set (`interface`, typed annotations, `: Promise<`,
    `enum`, `type X =`).
  - `_detect_tools()` — add content-based Docker detection (fix root cause 3):
    recognize Dockerfile directives and docker-compose structure, not just the
    literal `"docker"` string.
- **`tests/unit/test_skill_extractor.py`** — the source of truth for "done." No
  new tests strictly required, but I may add a couple of regression cases
  (e.g. arrow-function-only JS, `type` alias TS). The pre-existing typo on
  line 138 (`skill_names = [s.name for s in skill_names]`,
  `UnboundLocalError` in `test_database_technology_detection`) is a **separate**
  bug, out of scope for #148; I will note it but not fix it here unless asked.

### Plan

1. **Content-based JS detection.** In `_detect_languages()`, replace the
   whitespace-dependent regex with signals that match real code: `require(...)`
   (paren, optional space), ES6 `import ... from`, `export`, `const`/`let`,
   arrow functions (`=>`), and `async`/`await`. Collect these into
   `js_evidence`.
2. **Content-based TS detection.** Add TS-only signals — `interface X`,
   `type X =`, `enum`, and typed declarations / return types
   (`: string`, `: Promise<`, `<T>`). If any fire (or the filename is `.ts`),
   label the result `TypeScript`; otherwise `JavaScript`. Ensure a file that is
   both (JS signals + TS signals) resolves to TypeScript.
3. **Content-based Docker detection.** In `_detect_tools()`, add a helper that
   flags Docker when the text looks like a Dockerfile (`^FROM `, `RUN `,
   `EXPOSE `, `ENTRYPOINT`, `CMD `) or a compose file (`services:` plus
   `ports:`/`build:`/`image:`), in addition to the existing literal match.
4. **Run and verify.** `python3 -m pytest tests/unit/test_skill_extractor.py -q`
   — the four named tests go green with no regressions in the other JS/Python
   tests. Then run the full unit suite (`make test-unit`) to confirm nothing
   else breaks.
5. **Remove the `BUG(#148)` reproduction comments** added in commit `dd893af`
   and replace them with concise explanatory comments for the new logic.

### Inputs & outputs

- **Input:** `extract_skills(text: str, filename: Optional[str])` — the same
  signature; a raw source/documentation string and an optional filename.
- **Output:** a `list[SkillDetection]` sorted by confidence. After the fix, that
  list additionally includes `JavaScript` / `TypeScript` / `Docker` entries
  (each with a `name`, `category`, `confidence` in `[0, 1]`, and an `evidence`
  list) whenever the corresponding content signals are present.
- **No change** to the public API, dataclass shape, return type, or sort order.

### Risks & unknowns

- **Over-detection / false positives.** Broad JS signals like `const` or `=>`
  could fire on non-JS text (e.g. a shell arrow, a math `=>` in prose). Mitigation:
  require anchored / word-boundary patterns and prefer multiple weak signals over
  one, keeping confidence modest when evidence is thin.
- **JS-vs-TS precedence.** `test_mixed_language_text` mixes JS, Python, and TS in
  one string. I must make sure adding TS signals doesn't overwrite the JavaScript
  entry or vice-versa (they are keyed separately in `skills_dict`), and that both
  can coexist.
- **Docker heuristic scope.** Matching `FROM`/`RUN`/`EXPOSE` risks catching prose
  containing those words. Mitigation: anchor to line starts and/or require ≥2
  co-occurring directives before flagging.
- **Confidence formula.** Current confidence is `0.6 + n*0.1`; adding more
  evidence items shifts scores. `test_frameworks_detected_with_high_confidence`
  and `test_confidence_scores_are_floats` must still pass — keep the `min(0.95, …)`
  cap.
- **Unknown:** whether the extractor is exercised anywhere downstream (ingestion
  pipeline / RAG) in a way that depends on the current under-detection. Will grep
  usages before finalizing.

### Edge cases

- `require('fs')` and `require ('fs')` (with and without space).
- ES6 `import x from 'y'` vs. CommonJS `const x = require('y')`.
- TypeScript with **no** filename (content-only): `interface`, `type X = ...`,
  `enum`, `: Promise<User>`, `id: string`.
- A file that is both JS and TS → should resolve to TypeScript, not double-count.
- `.ts` / `.tsx` filename with empty or non-code body → still TypeScript by
  extension (preserve existing behavior).
- Dockerfile with only `FROM ...` (single directive) vs. full multi-directive file.
- docker-compose YAML with no literal `docker` string.
- Plain English prose containing words like "import", "class", or "from" →
  should **not** be misdetected as code (guard against false positives).
- Empty string and unrecognized-language input → still return a list (possibly
  empty), never raise.
