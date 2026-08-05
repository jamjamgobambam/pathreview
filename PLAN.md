# Solution plan

**Issue:** [#148 — Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148)

## Understand

The bug is in the ingestion pipeline's skill extractor — the component that reads resume and
portfolio text and reports which technologies a candidate has used. It detects Python,
frameworks, and databases, but the JavaScript/TypeScript family is effectively invisible to it,
and Docker is only found when the literal word "docker" appears.

**Expected vs. actual** (confirmed locally — see JOURNAL.md Week 8 for the full output):

| Input | Expected | Actual |
|---|---|---|
| `Wrote index.js using const arrow functions and async/await callbacks` | JavaScript | `[]` |
| `Built app.tsx and types.ts with strict TypeScript interfaces` | TypeScript | `['React']` |
| `const fs = require('fs')` | JavaScript | `[]` |
| `export interface User { id: string; }` | TypeScript | `['Python']` |
| Dockerfile (`FROM`/`RUN`/`EXPOSE`) | Docker | `['Python']` |
| compose YAML (`services:`/`build:`) | Docker | `[]` |

**Root cause** — five defects, all in `ingestion/parsers/skill_extractor.py`:

1. **`JS_TS_KEYWORDS` (lines 30–41) is dead code.** It is defined and never referenced anywhere
   in the repo (verified by grep). The set of signals it was meant to provide — `const`, `let`,
   `function`, `export`, `require` — is exactly what the failing tests supply, so JS detection
   has no working keyword path at all.
2. **The import regex cannot match `require(`.** `_detect_languages` (line 179) uses
   `re.search(r"\b(import|require)\s+", text)`, which requires whitespace after the keyword.
   `require('fs')` has a parenthesis, so it never matches.
3. **TypeScript is decided purely by filename** (line 186:
   `lang = "TypeScript" if ".ts" in str(filename or "").lower() else "JavaScript"`). For free text
   with no `filename` argument — the normal case for resume content — TypeScript can never be
   detected, even when the text literally says "TypeScript" and names `.ts` files.
4. **Docker is matched as a literal substring only.** `_detect_tools` (line 268) does
   `if tool in text_lower`, so real Dockerfile instructions or compose keys are never recognized.
5. **A false positive in the opposite direction:** because the same `\b(import|require)\s+` regex
   matches Python's `import` statements, plain Python code like `import psycopg2` is currently
   reported as **JavaScript**. Any fix must remove this, not just add detections.

A related quirk causes the TypeScript sample to be misreported as Python: the annotation regex
`:\s*(int|str|float|bool|list|dict)` (line 160) matches TypeScript's `: string`, because `str` is
a prefix of `string` and the pattern has no trailing word boundary.

**A successful fix** detects JavaScript and TypeScript from signals in the text itself (keywords
and syntax, not just filenames), detects Docker from Dockerfile and compose structure, stops
reporting Python imports as JavaScript, and leaves the Python, framework, React, and database
detection that already works untouched.

## Map

Files I expect to touch:

- **`ingestion/parsers/skill_extractor.py`** — the whole fix lives here:
  - `_detect_languages()` (lines 143–214): wire up `JS_TS_KEYWORDS`, replace the import regex,
    add text-based TypeScript signals, and add `\b` to the Python annotation pattern.
  - `_detect_tools()` (lines 263–276): add structural Docker detection alongside the existing
    keyword loop.
  - Possibly a new module-level constant for Dockerfile instructions and compose keys, following
    the existing `PYTHON_KEYWORDS` / `TOOLS` class-constant style.
- **`tests/unit/test_skill_extractor.py`** — add regression tests (see *Inputs & outputs*). The
  four tests named in the issue already exist and must go green; I'll add tests for the false
  positive and the TypeScript-from-prose case, which nothing currently covers.

Files I have checked and expect **not** to touch:

- `agent/tools/skill_extractor.py` — a different class with the same name (an agent `BaseTool`).
  Out of scope for this issue; I need to avoid editing it by mistake.
- Nothing else imports the parser `SkillExtractor` except its own test file (verified by grep),
  so the change has no production callers to break.

## Plan

1. **Establish the baseline.** Run `PYTHONUTF8=1 make test-unit` and record which tests fail
   before any change, so I can prove my change fixes the 4 target tests and breaks nothing else.
   (`PYTHONUTF8=1` is needed on Windows — see JOURNAL.md setup notes.)
2. **Fix JavaScript detection using the existing constant.** In `_detect_languages`, count how
   many distinct `JS_TS_KEYWORDS` appear as whole words in the text and treat that as evidence.
   Replace `\b(import|require)\s+` with patterns that match JS-flavored syntax specifically —
   `require(`, `import ... from`, `export` — so that `const fs = require('fs')` is detected.
3. **Remove the Python-import false positive.** Ensure the JS evidence path no longer fires on a
   bare Python `import x`. Verify with `import psycopg2`, which must report Python and not
   JavaScript.
4. **Add text-based TypeScript detection.** Detect TypeScript from signals in the text rather than
   only the filename: the word "typescript", `.ts`/`.tsx` references, `interface X {`,
   `Promise<...>`, and typed parameters like `(id: string)`. Keep the existing filename path
   working. Also add the missing `\b` to the Python annotation regex so `: string` stops counting
   as Python.
5. **Add structural Docker detection.** In `_detect_tools`, recognize Dockerfile instructions
   (`FROM`, `RUN`, `EXPOSE`, `COPY`, `WORKDIR`, `CMD`, `ENTRYPOINT`) and compose keys
   (`services:` with `build:`/`image:`/`ports:`), in addition to the current literal `docker`
   match, preserving the existing confidence value of 0.95.
6. **Write the regression tests** described in *Inputs & outputs*, following the existing file's
   patterns (`@pytest.mark.unit` on the class, the `extractor` fixture, and
   `skill_names = [s.name for s in result]` assertions).
7. **Verify.** Run `PYTHONUTF8=1 make test-unit` (all 4 target tests green, no new failures versus
   the step-1 baseline) and `make check` for ruff, black, and mypy, which the PR gate requires.

## Inputs & outputs

**Function being changed:** `SkillExtractor.extract_skills(text: str, filename: Optional[str] = None) -> list[SkillDetection]`

The public signature does **not** change. What changes is which `SkillDetection` objects come back
for a given input. Each detection carries `name`, `category`, `confidence` (0.0–1.0), and an
`evidence` list of human-readable strings, and the existing helpers mutate a shared `skills_dict`
in place — I'll keep both conventions.

| Input | Current output | Output after fix |
|---|---|---|
| `const fs = require('fs')` | `[]` | includes `JavaScript` (category `Language`) |
| `export interface User { id: string; }` | `['Python']` | includes `TypeScript`, no longer `Python` |
| `Built app.tsx and types.ts with strict TypeScript interfaces` | `['React']` | includes `TypeScript` (React may remain) |
| Dockerfile text | `['Python']` | includes `Docker` (category `Tool`, confidence 0.95) |
| compose YAML | `[]` | includes `Docker` |
| `import psycopg2` | `['Python', 'JavaScript']` | `Python` only — no JavaScript |
| `import os` / `def f():` (Python) | `['Python']` | unchanged |

New evidence strings will follow the existing wording style (e.g. `"JavaScript keywords found"`,
`"Dockerfile instructions found"`), since `evidence` is user-facing text in the review output.

**Tests I'll write** (in `tests/unit/test_skill_extractor.py`, matching its existing style):

```python
def test_python_imports_not_reported_as_javascript(self, extractor):
    """Plain Python imports should not trigger JavaScript detection."""
    result = extractor.extract_skills("import psycopg2\nimport os")
    skill_names = [s.name for s in result]
    assert "JavaScript" not in skill_names
    assert any("python" in s.lower() for s in skill_names)

def test_typescript_detected_from_prose_without_filename(self, extractor):
    """TypeScript should be detected from text alone, with no filename argument."""
    result = extractor.extract_skills("Built app.tsx and types.ts with strict TypeScript interfaces")
    skill_names = [s.name for s in result]
    assert any("typescript" in s.lower() for s in skill_names)

def test_dockerfile_without_the_word_docker(self, extractor):
    """A Dockerfile should be detected as Docker even without the literal word."""
    result = extractor.extract_skills("FROM node:20\nWORKDIR /app\nCOPY . .\nCMD [\"npm\", \"start\"]")
    skill_names = [s.name for s in result]
    assert any("docker" in s.lower() for s in skill_names)
```

## Risks & unknowns

1. **Loosening JS keyword matching could create new false positives.** `JS_TS_KEYWORDS` contains
   `import`, `async`, `await`, and `class`, which are all also Python keywords — so a naive
   "any keyword matches" rule would report every Python file as JavaScript, which is precisely
   the bug in root cause 5. My mitigation is to require either a JS-exclusive token
   (`const`, `let`, `var`, `function`, `export`, `require(`) or several keywords together, and to
   test `import psycopg2` explicitly. **This is the main design risk in the fix and I expect to
   iterate on the threshold.**
2. **Adding `\b` to the Python annotation regex at line 160 could regress Python detection.**
   `test_text_with_python_type_annotations` relies on that pattern. Reading the fixture, its text
   contains `url: str)` and `def`, both of which still match with a trailing `\b`, so I expect it
   to stay green — but this is an assumption I'll verify by running that specific test rather than
   assuming.
3. **TypeScript vs. JavaScript could double-count.** Line 187 writes to `skills_dict[lang]` with a
   single key, so it currently reports one or the other. If text contains both (a JS project with
   some TS files), I need to decide whether to emit both or prefer TypeScript. I lean toward
   emitting both, since `test_mixed_language_text` asserts more than one skill, but I'll confirm no
   existing test asserts an exact list length before deciding.
4. **The `.ts` filename check is a naive substring match** (`".ts" in filename.lower()`), so
   `data.tsv` or `notes.txt.ts.bak` would match. It's pre-existing and not in the issue; I'll
   likely tighten it to an extension check with `str.endswith`, but only if it doesn't grow the
   diff beyond the issue's scope.
5. **Out-of-scope failing test.** `test_database_technology_detection` also fails, but it isn't one
   of the four in the issue. It fails first on its own bug (line 138,
   `skill_names = [s.name for s in skill_names]` raises `NameError`), and I verified that even
   after fixing that line the assertion still fails because `psycopg2` isn't in the `DATABASES`
   map — only `postgresql` is. **Open question:** leave it alone and note it in the PR
   description, or fix it too? My current plan is to leave it out to keep the PR focused on #148.
6. **Confidence-score arithmetic.** Confidence is computed as
   `min(0.95, 0.6 + len(evidence) * 0.1)`, so adding evidence strings silently raises scores.
   `test_confidence_scores_are_floats` only checks the 0.0–1.0 range, so I'm not likely to break a
   test, but I should keep JS/TS confidence comparable to Python's rather than accidentally making
   every JS detection 0.95.

## Edge cases

The fix should handle each of these gracefully:

- **Plain Python with imports** (`import psycopg2`) — must report Python and **not** JavaScript.
  This is the regression risk I care most about.
- **TypeScript prose with no filename** (`"Built app.tsx and types.ts with strict TypeScript
  interfaces"`) — must report TypeScript; `filename` is `None`, which the code must not assume.
- **Dockerfile with no occurrence of the word "docker"** (`FROM node:20` / `WORKDIR /app`) — must
  report Docker.
- **docker-compose YAML** (`services:` / `build:` / `ports:`) — must report Docker without
  mistaking the YAML for a programming language.
- **Mixed JS + Python + TS in one document** (the existing `test_mixed_language_text` fixture) —
  must return more than one skill and must not crash on the overlapping keywords.
- **Empty string and plain English prose** — must return a list (possibly empty) and never raise;
  `test_empty_text` and `test_unrecognized_language` already assert this.
- **Ambiguous filenames** (`data.tsv`, `README.md` describing JavaScript) — a `.tsv` file should
  not be reported as TypeScript purely because `.ts` appears as a substring.
