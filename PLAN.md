## Solution plan

**Issue:** Issue #148 – Skill extractor fails to detect JavaScript and TypeScript

### Understand

The skill extractor does not correctly detect TypeScript from resume text when no `.ts` filename is provided. During testing, I found that TypeScript code such as `id: string` is incorrectly detected as Python because the Python regex matches `str` inside `string`. The current TypeScript detection also relies mainly on the `.ts` file extension instead of recognizing TypeScript syntax.

### Map

Files involved:

* `ingestion/parsers/skill_extractor.py`
* `tests/unit/test_skill_extractor.py`

### Plan

1. Review the Python detection regex to prevent TypeScript syntax from being identified as Python.
2. Improve the JavaScript and TypeScript detection logic so it recognizes language-specific syntax instead of relying mainly on file extensions.
3. Update or add unit tests to verify JavaScript and TypeScript detection.
4. Run the relevant unit tests and confirm the issue is resolved without breaking existing behavior.

### Inputs & outputs

**Input:**

* Resume text containing JavaScript, TypeScript, or Python code.
* Optional filenames such as `.js`, `.ts`, or `.py`.

**Output:**

* JavaScript resumes should detect JavaScript.
* TypeScript resumes should detect TypeScript.
* Python resumes should continue to detect Python correctly.
* TypeScript syntax should no longer be incorrectly detected as Python.

### Risks & unknowns

* JavaScript and TypeScript share similar syntax, so the detection rules must avoid misclassifying one as the other.
* Changes to the Python detection regex could affect existing Python detection.
* Additional patterns may be needed after running the unit tests.

### Edge cases

* TypeScript code without a `.ts` filename.
* JavaScript code without a `.js` filename.
* Mixed-language resumes.
* Valid Python type annotations such as `name: str`.
* TypeScript annotations such as `name: string`.
