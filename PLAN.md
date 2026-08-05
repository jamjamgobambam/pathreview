## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace - https://github.com/ascherj/pathreview/issues/147

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause of this issue is that the section header detection logic in `ResumeParser` uses regular expression patterns that strictly anchor headers to the start of a line without permitting leading indentation (whitespace/tabs). This causes indented headers in resumes (extracted from PDFs or Markdown) to fail to match and `detected_sections` returns empty.

The expected behavior is that the section header detection logic should permit optional leading whitespace (e.g., `^[ \t]*`) before section headers, enabling reliable detection across all resume formats. 
The actual behavior is that the section header detection logic fails to detect headers with leading indentation, resulting in empty `detected_sections`.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

* `ingestion/parsers/resume_parser.py`

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

* Modify `_detect_sections` in `ingestion/parsers/resume_parser.py` to permit optional leading whitespace before section headers in regular expression patterns.
* Add or update regex patterns to allow `^[ \t]*` (zero or more spaces/tabs) before `section` in patterns like `rf"^[ \t]*{re.escape(section)}\s*$"` and `rf"^[ \t]*{re.escape(section)}\s*[:|-]"`.
* Run `pytest tests/unit/test_resume_parser.py` to verify that all section detection tests pass with the change.
* Run `ruff check --fix ingestion/parsers/resume_parser.py` and `black ingestion/parsers/resume_parser.py` to ensure code quality and formatting.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The input is the content of a resume, either in PDF bytes or Markdown string format. The output should be a `ParseResult` object with the full extracted text and metadata including detected sections (e.g., "Experience", "Education", "Skills"). The fix should modify the `_detect_sections` method in `ResumeParser` to correctly identify section headers even when they have leading indentation.

### Risks & unknowns
What could go wrong? What are you still unsure about?
One potential risk is that overly broad regex patterns might inadvertently match unintended text, but the current approach uses a fixed set of known section headers and anchors patterns with `\s*$`, so this risk should be minimal. I'm not currently aware of any specific unknowns or edge cases beyond what's already been identified in the issue description.

### Edge cases
What inputs or states should your fix handle gracefully?
The fix should handle resumes with varying indentation levels, blank lines between sections, and different section header formatting (e.g., with colons, hyphens, or just the header text alone). It should also gracefully handle resumes with no work experience or other common sections by returning an empty list for those sections rather than failing or producing incorrect results.