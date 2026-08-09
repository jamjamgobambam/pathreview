## Solution plan

**Issue:** [#147 Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- **Root Cause:** The regular expressions used in the parser to identify headers and markdown syntax likely start strictly to the beginning of a line without accounting for leading spaces or tabs.
- **Expected:** The parser should correctly identify headers even if they are indented with spaces or tabs.
- **Actual:** The parser returns an empty list for sections, and fails to strip markdown headers if leading whitespace exists.

### Map
Which files, functions, or modules are involved?
- `ingestion/parsers/resume_parser.py`
  - Function: `_detect_sections()`
  - Function: `_strip_markdown()` (also failing due to the same root cause)

### Plan
What are the steps to fix this issue?
1. Open `resume_parser.py` and locate the regex patterns used to match sections and markdown headers.
2. Update the regex patterns to allow for optional leading whitespace. Reseaching solutions shows this typically involves adding `^[ \t]*` or `^\s*` before the header keyword match.
3. Apply the same whitespace-tolerant logic to the `_strip_markdown()` function.
4. Run the test suite (`pytest tests/unit/test_resume_parser.py`) to verify that all 6 currently failing tests turn green.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- **Input:** Raw string text extracted from PDFs or Markdown files containing headers preceded by spaces/tabs.
- **Output:** A properly populated list of strings (e.g., `['Experience', 'Education', 'Skills']`) extracted and assigned to `result.metadata["detected_sections"]`.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- **Risk:** If we make the regex *too* loose by using generic whitespace matching like `\s*`, it might accidentally match multi-line text artifacts or bullet points mid-sentence that happen to look like headers. We need to be careful to only target spaces and tabs (`[ \t]*`) at the start of a line.

### Edge cases
What inputs or states should your fix handle gracefully?
- Mixed spaces and tabs used for indentation.
- Headers that have trailing whitespace before the colon (e.g., `Experience :`).