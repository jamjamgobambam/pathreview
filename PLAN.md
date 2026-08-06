## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace 
[link](https://github.com/ascherj/pathreview/issues/147)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause is that `_detect_sections()` only matches section headers that begin at the start of a line, so lines like `  Experience:` or `    Education:` do not match. The expected behavior is that section detection should ignore leading whitespace and still recognize normal resume headers; the actual behavior is that those headers are skipped and the parser returns incomplete or empty `detected_sections` metadata.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The main file is [ingestion/parsers/resume_parser.py](ingestion/parsers/resume_parser.py), specifically `_detect_sections()` and possibly `_strip_markdown()` if normalization is needed there. I also expect to update or add a regression test in [tests/unit/test_resume_parser.py](tests/unit/test_resume_parser.py).

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Update `_detect_sections()` so section-header matching tolerates leading whitespace before the header text.
2. Add or extend a unit test that uses resume text with indented section headers and asserts the sections are still detected.
3. Verify the existing section-detection cases still pass for unindented headers and markdown resumes.
4. Run the focused resume parser tests to confirm the regression is fixed.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input is resume text from Markdown or extracted PDF text, including lines that may begin with spaces or tabs. The fix should produce the same parsed text as before, but `metadata["detected_sections"]` should include headers such as Experience and Education even when they are indented.

### Risks & unknowns
What could go wrong? What are you still unsure about?

The main risk is making the header regex too permissive so it matches a section keyword that appears mid-sentence in body text. Concrete false positives to guard against:

- `I have experience with Python` must **not** be detected as an *Experience* header.
- `Fluent in three languages` must **not** match `languages`.
- `Delivered several projects on time` must **not** match `projects`.

Keeping the `^`/`\n` line anchors prevents these, because the keyword is not at the (optionally indented) start of a line.

The whitespace-class choice is the key decision here. `\s` matches vertical whitespace (`\n`, `\r`, `\f`, `\v`) in addition to spaces and tabs, so `^\s*experience` could let the class consume a trailing newline and match `experience` on the *following* line, or span a blank-line gap — reintroducing exactly the false positives the anchor is meant to prevent. `[ \t]*` restricts tolerance to true horizontal indentation, which is precisely the leading-whitespace case in issue #147, so it is the tighter change.

A secondary risk is regressing detection for multi-word headers such as `Technical Skills` or `Work Experience`; the fix touches only the leading anchor, not the `re.escape(section)` body, so these should be unaffected — but they need an explicit test.

### Edge cases
What inputs or states should your fix handle gracefully?

The fix should handle headers with leading spaces, multiple leading spaces, and a mix of indented and unindented section titles. It should still work when section names have trailing punctuation like `Skills:` or `Experience -` and should not break markdown parsing or PDF-derived text that already contains section headings at column 0.