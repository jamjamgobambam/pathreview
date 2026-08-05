## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/147

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is in `ingestion/parsers/resume_parser.py`. The `_detect_sections()`
function looks for section headers (like "Experience" or "Education") using regex
patterns that expect the header to start right at the beginning of a line, with no
space in front. PDF text extraction often keeps the original indentation, so a header
like `    Education` has leading spaces and matches none of the patterns.

- **Expected:** The parser finds sections such as "Education" and "Skills" even when
  the lines are indented.
- **Actual:** `detected_sections` comes back as an empty list whenever the text is
  indented, so all section info for the resume is lost.

The same problem exists in `_strip_markdown()`, whose header regex `^#+\s+` cannot
strip an indented markdown header like `    # Summary`.

### Map
Which files, functions, or modules are involved?

- `ingestion/parsers/resume_parser.py`
  - `_detect_sections()` — the four header regex patterns
  - `_strip_markdown()` — the markdown-header regex
- `tests/unit/test_resume_parser.py` — the failing tests that confirm the fix
  (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
  `test_detect_sections`)

### Plan
What are the steps to fix this issue? Break it into 3–5 concrete sub-tasks.

1. Reproduce the bug by parsing indented resume text and confirming
   `detected_sections` is empty.
2. Add `\s*` right after each `^` and `\n` anchor in the four patterns inside
   `_detect_sections()` so leading whitespace is allowed.
3. Do the same in `_strip_markdown()`: change `^#+\s+` to `^\s*#+\s+` so indented
   markdown headers are stripped.
4. Run the failing tests and confirm they now pass, and that no other tests break.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** Resume text (from a PDF or markdown) that may have leading whitespace
  in front of section headers.
- **Output / change:** `_detect_sections()` returns the correct list of section names
  (e.g. `["Education", "Skills"]`) regardless of indentation, and `_strip_markdown()`
  removes indented markdown headers. No change to the public API or return shape.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Adding `\s*` makes the patterns a bit looser, so an indented line that happens to
  equal a section word could now be detected as a header. In practice this is fine
  because the patterns still require the header to be alone on the line or followed
  by `:`, `|`, or `-`.
- The fix does not handle headers written in mixed order or with extra characters;
  it only addresses leading whitespace, which is what the issue asks for.

### Edge cases
What inputs or states should your fix handle gracefully?

- Headers indented with spaces or tabs (`    Education`, `\tSkills`).
- Headers at the very start of the text vs. after a newline.
- Headers followed by `:`, `|`, or `-`, or standing alone on a line.
- Markdown headers that are indented (`   ## Summary`).
- Text with no section headers at all — should still return an empty list without
  errors.
