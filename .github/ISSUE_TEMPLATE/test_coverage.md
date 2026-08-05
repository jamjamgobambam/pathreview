---
name: Test Coverage
about: Add or improve test coverage
labels: tests
---

## What Needs Testing?
`StructuralChunker.chunk()` needs regression coverage for non-empty documents where `_extract_sections()` returns no structural sections.

## Current State
The structural chunker suite covered empty input and heading-based documents but did not assert that headingless documents were returned as chunks. The missing assertion allowed the empty-section path to silently return `[]`.

## Scenarios to Cover
- Plain text without headings returns one semantic chunk with original text and source metadata.
- Large headingless text returns multiple non-empty semantic chunks and retains every source sentence.
- A headingless bullet list is retained as content.
- `#hashtag` text without a space is treated as content, not a Markdown heading.
- Headingless semantic chunks do not receive `heading_path` or `heading_level` metadata.
- Caller-provided metadata remains unchanged.

## Test Level
- [x] Unit
- [ ] Integration
- [ ] End-to-end
- [ ] Security

No testing was added for Integration, End-to-end, or Security. These were beyond the scope of this pull request. 

## Relevant Files
- `ingestion/chunking/structural_chunker.py`
- `tests/unit/test_structural_chunker.py`

## Acceptance Criteria
- [x] Tests follow existing patterns in `tests/`.
- [x] Each listed scenario has an assertion for its expected behavior.
- [x] New tests pass locally with `pytest tests/unit/test_structural_chunker.py -m unit`.
- [x] Relevant existing structural-chunker tests pass.
