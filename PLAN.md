## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace  
https://github.com/ascherj/pathreview/issues/147

### Understand

The `_detect_sections()` function in `ingestion/parsers/resume_parser.py` uses regular expressions to identify resume sections such as Education, Skills, and Experience. The current patterns expect the section name to appear directly at the beginning of a line.

The expected behavior is for the function to recognize section titles even when spaces or tabs appear before them. For example, resume text containing indented `Education:` and `Skills:` lines should return both sections.

The actual behavior is that `_detect_sections()` returns an empty list because the spaces before the section names prevent the regular expressions from matching them.

The root cause is that the current patterns do not allow optional whitespace between the beginning of the line and the section name.

### Map

The main files involved are:

- `ingestion/parsers/resume_parser.py`
  - `_detect_sections()` contains the regular expressions that need to be updated.
  - `SECTION_HEADERS` contains the recognized section names, but I do not expect to change it.

- `tests/unit/test_resume_parser.py`
  - This file contains the existing tests for resume section detection.
  - I added `test_detect_sections_with_leading_whitespace` to reproduce the issue.
  - I will use the existing tests to make sure the fix does not break the current behavior.

### Plan

1. Keep the new test that uses resume text with spaces before `Education:` and `Skills:`. The test should expect both sections to be detected and should fail before the fix is applied.

2. Update the regex patterns inside `_detect_sections()` so they allow optional spaces or tabs before a section name.

3. Review whether the patterns that begin with `\n` are still necessary. Since the function uses `re.MULTILINE`, the patterns beginning with `^` may already cover section titles at the beginning of every line.

4. Run the tests in `tests/unit/test_resume_parser.py` and confirm that the new test and the existing resume parser tests pass.

5. Test additional examples to make sure normal sentences containing words such as Experience or Skills are not incorrectly detected as section titles.

### Inputs & outputs

The input is a string of resume text. Some of the lines might start with spaces or tabs, either because the original resume was formatted that way or because the text came from a PDF and kept extra indentation.

The output is the list of section names the parser finds.

I am not changing the function signature or return type. The only behavior change should be that indented section titles are now recognized. For the example from the issue, the result should include `Education` and `Skills`.

### Risks & unknowns

The main risk is accidentally creating false matches. If I make the regex too loose, a normal sentence could get treated as a section header just because it starts with a word like Experience or Skills. The rest of the pattern should help because it still requires a delimiter or the end of the line, but I want a test for that so I am not just assuming it works.

I also need to decide whether the two patterns that start with `\n` are still worth keeping. Leaving them in would be the smallest change, but removing them may make the code easier to read because `re.MULTILINE` already lets `^` match the beginning of each line.

Another choice is whether to use `\s*` or something more specific like `[ \t]*`. I am leaning toward `[ \t]*` because `\s` can also match line breaks, and I do not want the fix to be broader than it needs to be.

### Edge cases

I want the fix to handle:

- Section titles with leading spaces
- Section titles with leading tabs
- Section titles with both spaces and tabs
- Section titles with trailing spaces
- Section titles followed by a colon, vertical bar, or hyphen
- Blank lines between resume sections
- Windows line endings using `\r\n`
- Empty resume text
- Resume text with no recognized section titles

It should not detect a section when the section word is only part of a normal sentence, such as `My Experience at TechCorp`.
