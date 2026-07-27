## Solution plan

**Issue:** [Resume section detection fails on text with leading whitespace](https://github.com/ascherj/pathreview/issues/147)

### Understand

`ResumeParser._detect_sections()` (`ingestion/parsers/resume_parser.py:127-146`) is supposed to detect
which resume sections (Education, Skills, Experience, etc.) are present in the parsed text, so that
metadata like `detected_sections` reflects what's actually in the document.

Its regex patterns anchor the section keyword directly to the start of a line or right after a
newline (`^{section}`, `\n{section}`), with no allowance for leading whitespace. Text extracted from
PDFs — and any Markdown/plain text that happens to be indented — commonly has spaces or tabs before a
header like `Education:`, so none of the four patterns match and the header is silently skipped.

- **Expected:** `_detect_sections("        Education:\n...")` returns `["Education"]`.
- **Actual:** it returns `[]` — the section is present in the text but not detected, even though
  nothing else about the resume is malformed.

This isn't hypothetical — five existing tests in `tests/unit/test_resume_parser.py` already fail
against current `main` because their fixture text is indented (an artifact of using indented
triple-quoted strings), and the new `test_detect_sections_with_leading_whitespace` test added in the
reproduction commit fails the same way in isolation.

### Map

Files/functions expected to be touched:

- `ingestion/parsers/resume_parser.py` — `_detect_sections()`, the regex patterns themselves (core fix).
- `tests/unit/test_resume_parser.py` — the reproduction test added this week will flip from failing to
  passing; may add 1-2 more targeted cases (tabs, mixed indentation).
- No changes expected in `ingestion/pipeline.py`, `api/`, or `frontend/` — `_detect_sections()` is a
  private, pure-text-in/list-out method with no external dependents beyond `_parse_pdf` /
  `_parse_markdown`, which just pass its return value through into `metadata["detected_sections"]`.

### Plan

1. Update the four regex patterns in `_detect_sections()` to tolerate leading horizontal whitespace
   before the section keyword — e.g. insert `[ \t]*` right after each `^` and `\n` anchor:
   `rf"^[ \t]*{re.escape(section)}\s*$"`, etc.
2. Re-run the existing suite (`pytest tests/unit/test_resume_parser.py`) and confirm the previously
   failing indentation-related tests (`test_parse_single_column_resume_text`,
   `test_parse_resume_no_work_experience`, `test_parse_markdown_resume`, `test_detect_sections`,
   `test_detect_sections_with_leading_whitespace`) now pass.
3. Add a couple of small additional regression cases to lock in the fix: headers indented with tabs,
   and a header with no leading whitespace at all (to confirm the fix doesn't loosen matching to the
   point of false positives, e.g. matching "Education" inside unrelated indented prose).
4. Leave `test_strip_markdown_syntax` as a separate, pre-existing failure — its root cause is a
   different regex (`_strip_markdown`'s `^#+\s+` header-stripping pattern, same whitespace-anchoring
   bug family but a different method/behavior) and is out of scope for issue #147 specifically. Flag it
   as a follow-up rather than silently fixing it in the same PR.
5. Run `make check && make test-unit` before opening the PR, per `CONTRIBUTING.md`.

### Inputs & outputs

- **Input:** the plain-text (already-extracted) resume string passed into `_detect_sections(text)` —
  this is text that has already gone through PDF extraction (`pypdf`) or markdown-stripping
  (`_strip_markdown`), so it may contain arbitrary leading whitespace/indentation per line, mixed
  spaces/tabs, and varying blank-line spacing.
- **Output:** unchanged shape — a deduplicated `list[str]` of title-cased section names (e.g.
  `["Education", "Skills"]`) — but now inclusive of sections whose header line is indented, matching
  the existing contract that `metadata["detected_sections"]` reflects sections actually present in the
  document.

### Risks & unknowns

- **Over-matching:** loosening the anchor with `[ \t]*` could start matching a section keyword that
  appears indented as part of unrelated body text (e.g. a bullet point that says "  skills:" under an
  unrelated heading). Mitigating this is why step 3 adds a false-positive regression case.
- **Non-space whitespace:** unclear whether real-world PDF extraction ever produces other whitespace
  characters (e.g. non-breaking spaces `\xa0`) before headers; `pypdf`'s `extract_text()` behavior here
  is not something I've verified against a real sample PDF yet, only synthetic text fixtures.
- **Same-bug-family fallout:** `_strip_markdown`'s header pattern has the identical anchoring flaw;
  need to confirm with reviewers/maintainer whether that should be filed as its own follow-up issue or
  is expected to be bundled into this fix.

### Edge cases

- Section header with leading spaces (`"    Education:"`).
- Section header with leading tabs (`"\tSkills:"`).
- Section header with no leading whitespace at all (must still match, no regression).
- Section header preceded by a blank/whitespace-only line.
- Text where a section keyword appears indented mid-sentence, not as a header (should NOT be detected
  as a section).
- Empty string / text with no section headers at all (must return `[]` without raising).
