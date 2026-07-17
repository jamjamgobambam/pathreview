# Solution Plan

**Issue:** #147 — Resume section detection fails on text with leading whitespace

**GitHub Issue:** https://github.com/ascherj/pathreview/issues/147

---

## Understand

The resume parser currently fails to detect common resume sections when section headers contain leading whitespace. During investigation and local reproduction, I confirmed that `_detect_sections()` returns an empty list for resume text containing indented section headers such as `Education:` and `Skills:`, even though these are valid resume sections. The current implementation searches for section headers using regular expressions anchored to the beginning of each line and does not account for leading indentation. The expected behavior is for section detection to work regardless of leading whitespace, which commonly occurs after text extraction from PDF documents.

**Current understanding of the root cause:**

The regular expression patterns used by `ResumeParser._detect_sections()` anchor section headers at the beginning of each line and do not account for leading indentation. This matches the behavior observed during local reproduction and is the primary area I plan to investigate during implementation.

---

## Map

### Files investigated

* `ingestion/parsers/resume_parser.py`

  * `ResumeParser.parse()`
  * `ResumeParser._parse_pdf()`
  * `ResumeParser._parse_markdown()`
  * `ResumeParser._detect_sections()`

* `tests/unit/test_resume_parser.py`

  * `test_parse_single_column_resume_text`
  * `test_parse_resume_no_work_experience`
  * `test_detect_sections`

### Files I currently expect to modify

* `ingestion/parsers/resume_parser.py`
* `tests/unit/test_resume_parser.py` (only if additional regression coverage is needed)

---

## Plan

1. Review the existing regular expression patterns used by `_detect_sections()` and determine the smallest change that allows indented section headers to be recognized.
2. Update `_detect_sections()` while preserving its existing public behavior and supported section-header formats.
3. Re-run the three reproduced failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, and `test_detect_sections`) to verify that the targeted issue has been resolved.
4. Run the remaining resume parser tests to confirm the change does not introduce regressions.
5. Add or update a regression test if additional coverage is needed, then run the project's quality checks before committing the implementation.

---

## Inputs & Outputs

**Function being modified**

`ResumeParser._detect_sections(text: str) -> list[str]`

**Current input**

Resume text that may contain leading whitespace before section headers.

**Current output**

Returns an empty list when valid section headers are indented.

**Expected output**

Returns the detected section names regardless of leading indentation while preserving the existing behavior for already-supported inputs.

No public API changes are expected.

---

## Risks & Unknowns

1. `_detect_sections()` currently supports multiple section-header patterns. I need to verify that any regular expression changes preserve all existing matching behavior rather than fixing one pattern while unintentionally breaking another.

2. While reproducing this issue, I observed additional failing tests involving `_strip_markdown()`. Based on my investigation, those failures currently appear unrelated to Issue #147, so I intend to keep this implementation focused on `_detect_sections()` unless further investigation demonstrates a dependency between the two behaviors.

3. I have not yet determined whether the existing failing tests provide sufficient regression coverage or whether an additional dedicated test should be added. I'll inspect the current test coverage before making that decision.

---

## Edge Cases

* Section headers preceded by spaces or tabs (the primary scenario addressed by this issue).
* Resumes containing a mixture of indented and non-indented section headers.
* Resumes without an `Experience` section should continue to detect other valid sections such as `Education` and `Skills`.
* Existing resumes that already pass section detection should continue producing the same detected sections after the implementation.
