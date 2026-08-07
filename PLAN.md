## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of this issue is that the regex patterns in _detect_sections() of ingestion/parsers/resume_parser.py anchor the section name directly to the start of a line, leaving no room for leading whitespaces. The expected behavior is that the _detect_sections should recognize the section headers of the resume regardless of leading whitespaces. The actual behavior is that the function returns an empty list of detected sections since there is leading whitespaces before the header word in the indented input.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- ingestion/parsers/resume_parser.py
    - Function: _detect_sections(self, text: str)
- Test file: tests/unit/test_resume_parser.py
    - Failed tests that are related to this issue: test_parse_single_column_resume_text, test_parse_resume_no_work_experience, test_detect_sections

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Update the regex patterns in _detect_sections to allow optional leading whitespace between the line-start anchor and the section header word
2. Rerun the reproduction bug logic in detect_sections_bug.py to confirm that the sections of resume are detected.
3. Run the unit tests (tests/unit/test_resume_parser.py) for the parser to confirm that the three related tests above are passed.
4. Verify a non-indented section header still detects correctly.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

My fix takes the current regex patterns that only match the section headers that does not contain leading whitespaces, which will return an empty list. It should produce the regex patterns that also match the section headers that preceded by the whitespaces, so it can return the detected section names as the list.

### Risks & unknowns
What could go wrong? What are you still unsure about?

This could go wrong by having a section header word inside a sentence and has the word as a substring of another word. These words are not the section headers, so they should not be detected. It will also go wrong on absorbing newlines as the leading whitespaces, since whitespaces are the spaces before the word on the same line, which means it does not count any newlines.

### Edge cases
What inputs or states should your fix handle gracefully?

Non-indented headers still have to be detected. Mixed indentation will be depended on the amount or type of leading whitespaces. Header as mid-sentence word and substring words should not be detected since they are not the section headers. The first line of the whole text have to be detected. The headers that have trailing whitespaces after them still have to be detected. Duplicate headers have to be detected once.