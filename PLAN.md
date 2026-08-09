# PLAN

## Solution plan

**Issue:** [Skill extractor fails to detect JavaScript and TypeScript](https://github.com/ascherj/pathreview/issues/148)

### Understand

`SkillExtractor._detect_languages()` does not reliably recognize JavaScript or
TypeScript when `extract_skills()` receives source text without a filename.
On `origin/main`, JavaScript evidence recognizes `require` only when whitespace
follows it, so the common `require("module")` form is missed. TypeScript is
identified primarily from a `.ts` filename, so content containing declarations
such as `interface` and annotations such as `name: string` is missed when no
filename is supplied.

The expected behavior is for the extractor to return JavaScript or TypeScript
`SkillDetection` objects for common language syntax as well as recognized file
extensions. The actual behavior on `origin/main` is that the focused
`test_javascript_detection` and `test_text_with_typescript_files` tests fail.
The failure and passing feature-branch result are recorded in
`issue-148-reproduction.txt`.

**Root cause:** In `SkillExtractor._detect_languages()`, the original shared
JavaScript/TypeScript evidence block only matches `require` when whitespace
follows the word, but CommonJS calls use an opening parenthesis. The block also
chooses TypeScript only when the optional filename contains `.ts`; it has no
content patterns for TypeScript declarations or annotations.

### Map

**Relevant file map**

1. `ingestion/parsers/skill_extractor.py` — contains the parser-side
   `SkillDetection` result type and `SkillExtractor`. `extract_skills()` (around
   lines 108–141) coordinates detection and sorts results;
   `_detect_languages()` (around lines 143–230) contains the issue #148 logic.
2. `tests/unit/test_skill_extractor.py` — directly imports the ingestion parser.
   `test_text_with_typescript_files` (around line 46) and
   `test_javascript_detection` (around line 173) reproduce the two failures;
   filename, mixed-language, confidence, and empty-input tests protect adjacent
   behavior.
3. `agent/tools/skill_extractor.py` — defines a separate agent `BaseTool` with
   the same class name. It scans explicit skill names in resume text and
   repository metadata and returns a categorized dictionary. It does not import
   the ingestion parser and is outside this issue's implementation scope.
4. `issue-148-reproduction.txt` — records the two failures on `origin/main` and
   the passing focused tests on the feature branch.
5. `docs/ARCHITECTURE.md` — establishes that `ingestion/` and `agent/` are
   separate subsystems, confirming the boundary between the two skill
   extractors.
6. `docs/CONTRIBUTING.md` — requires tests for code changes, Google-style public
   docstrings, Conventional Commits, and `make check` plus `make test-unit`
   before a pull request.
7. `pyproject.toml` — defines the Python 3.11 target, pytest unit marker, and the
   Ruff, Black, and mypy settings that the change must satisfy.

**Data flow**

1. A caller supplies source text and, optionally, a filename to
   `SkillExtractor.extract_skills()`.
2. `extract_skills()` creates a dictionary keyed by canonical skill name and
   passes it to `_detect_languages()`, followed by the framework, React,
   database, and tool detectors.
3. `_detect_languages()` converts matching syntax or filename evidence into
   `SkillDetection` objects. Using the skill name as the dictionary key prevents
   duplicate entries.
4. `extract_skills()` sorts all detections by descending confidence and returns
   a list. This parser performs no database writes or other external side
   effects.
5. The unit tests call this flow directly and assert against the returned skill
   names and result structure.

Repository search found no production import of
`ingestion.parsers.skill_extractor`; its current behavior is exercised directly
by `tests/unit/test_skill_extractor.py`. The similarly named agent tool follows
an independent `execute()` → `_extract_skills()` flow and should not be changed
for issue #148.

**Patterns to preserve**

- Evidence is accumulated in lists and included in every `SkillDetection`.
- Confidence uses the existing `min(0.95, 0.6 + evidence_count * 0.1)` cap.
- The shared dictionary provides one result per canonical skill name.
- Public methods retain type hints and Google-style docstrings.
- Tests use the existing pytest fixture and direct assertions on returned skill
  names.
- Validation follows the documented `make check` and `make test-unit` workflow.

### Plan

1. Reproduce both failures on `origin/main` with the focused unit tests and
   record the expected and actual detected skill names.
2. Separate JavaScript and TypeScript evidence collection in
   `_detect_languages()`, adding focused evidence for `.js`/`.jsx` and
   `.ts`/`.tsx` filenames, `require(...)`, JavaScript declarations, TypeScript
   declarations, and primitive type annotations.
3. Create the corresponding `SkillDetection` objects while preserving the
   existing language category, bounded confidence calculation, evidence lists,
   and sorted return structure.
4. Verify filename-free, filename-based, and mixed-language cases with the
   focused tests and the neighboring language-detection tests.
5. Run the complete skill-extractor test module, confirm no regressions, and
   document any unrelated pre-existing failure separately.

### Inputs & outputs

**Function being changed:**
`SkillExtractor._detect_languages(text: str, filename: str | None, skills_dict: dict) -> None`

**Inputs**

- Source-code or documentation text passed to `extract_skills()`.
- An optional filename that may supply a language extension.

**Outputs**

- A sorted list of `SkillDetection` objects.
- JavaScript evidence produces a `JavaScript` detection.
- TypeScript evidence produces a `TypeScript` detection.
- Each detection retains its language category, confidence score between 0 and
  1, and concrete evidence strings.

**Acceptance test specification**

The existing focused tests already express the two regressions, so they should
remain the primary acceptance tests rather than adding redundant coverage:

```python
def test_language_detection_without_filename(extractor):
    cases = [
        ("const fs = require('fs');", "JavaScript"),
        ("interface User { id: string; }", "TypeScript"),
    ]

    for text, expected in cases:
        result = extractor.extract_skills(text)
        assert expected in [skill.name for skill in result]
```

For both cases, the expected output contains a language `SkillDetection` with
at least one matching evidence string. The fix must not require a filename and
must not change the result structure.

### Risks & unknowns

- JavaScript, TypeScript, and Python share tokens such as `import`, `async`, and
  `class`; overly broad regular expressions in `_detect_languages()` could
  create false positives.
- TypeScript is a superset of JavaScript, so a mixed set of evidence may
  reasonably produce both detections. Tests must clarify rather than assume
  exclusivity.
- Matching generic words such as `type` in prose could incorrectly report
  TypeScript; patterns should require declaration or annotation structure.
- Confidence scoring changes could reorder results consumed elsewhere, so the
  existing bounded scoring formula and sorted output should remain intact.
- The full test module contains an unrelated PostgreSQL test that references
  `skill_names` before assigning it; that failure should not be attributed to
  issue #148.
- Repository search currently finds no production caller for the ingestion
  parser. The fix can be verified at the parser contract and unit-test level,
  but wiring it into the separate agent tool would be a different issue and
  must not be added to this scope without maintainer direction.

### Edge cases

- JavaScript using `require("module")` with no filename.
- JavaScript using ES module imports or `const`, `let`, and `var`.
- TypeScript interfaces, type aliases, enums, namespaces, and primitive
  annotations with no filename.
- Upper- or lower-case `.js`, `.jsx`, `.ts`, and `.tsx` filenames.
- Mixed Python, JavaScript, and TypeScript text should return every supported
  language for which evidence exists.
- TypeScript syntax that also supplies JavaScript evidence may return both
  languages; results must remain unique by skill name.
- Empty input and unrecognized text should return no new JavaScript or
  TypeScript detections.
- Prose containing isolated words such as “type” or “interface” should not be
  detected unless it matches declaration structure.
