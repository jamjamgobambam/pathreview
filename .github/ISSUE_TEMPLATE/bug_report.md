---
name: Bug Report
about: Something isn't working as expected
labels: bug
---

## Describe the Bug
`StructuralChunker` silently discarded non-empty Markdown documents that contained no valid ATX headings. This affected plain-text documents, headingless lists, and text beginning with a hashtag not followed by a space, preventing their content from reaching downstream ingestion and retrieval.

## To Reproduce
1. Check out `main` and activate the project virtual environment.
2. Run:
	```bash
	python -c 'from ingestion.chunking.structural_chunker import StructuralChunker; print(StructuralChunker().chunk("Plain text without Markdown headings.", {"source": "repro"}))'
	```
3. Observe that the command prints `[]` despite receiving non-empty content.

## Expected Behavior
A non-empty document without Markdown headings should produce one or more semantic chunks, retain its content, and preserve supplied source metadata. Heading metadata should be absent because no valid heading exists.

## Actual Behavior
`StructuralChunker._extract_sections()` returned an empty list for headingless input. `StructuralChunker.chunk()` then iterated over that list and returned no chunks without raising an error.

## Environment
- OS: macOS
- Python version: 3.13.13
- Dependency/environment manager: project virtual environment (`.venv-1`)
- Commit or branch: `main` before the fix; `fix/149-structural-chunker-silently-drops-documents-with-no-headings` contains the fix

## Relevant Files
- `ingestion/chunking/structural_chunker.py`
- `tests/unit/test_structural_chunker.py`

## Acceptance Criteria
- [x] The reproduction steps return a semantic chunk instead of `[]` on the fix branch.
- [x] Regression tests cover plain text, large headingless content, bullet lists, and non-heading hashtag text.
- [x] The focused structural chunker unit suite passes.
