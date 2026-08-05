# Title
fix: Routes headingless content through semantic chunking so documents are retained while preserving their source metadata.

## Summary
`StructuralChunker` silently dropped non-empty Markdown documents that did not contain valid headings because section extraction returned an empty list and no fallback ran. This PR routes headingless content through semantic chunking so documents are retained while preserving their source metadata.

## Issue
Closes Issue #149

## Changes
The root cause was that `StructuralChunker.chunk()` treated an empty result from `_extract_sections()` as a completed chunking operation. Documents with plain text, bullet lists, or hashtag text without a Markdown heading therefore produced zero chunks.

- `ingestion/chunking/structural_chunker.py`: fix: now falls back to `SemanticChunker.chunk()` when structural section extraction returns no sections.
- `tests/unit/test_structural_chunker.py`: fix: strengthened the headingless-document test to assert content and metadata preservation without mutating the caller's metadata.
- `tests/unit/test_structural_chunker.py`: addded coverage for large headingless content that requires multiple semantic chunks, headingless bullet lists, and `#hashtag` text that is not a valid Markdown heading.
- `tests/unit/test_structural_chunker.py`: tightened existing assertions for heading paths and non-empty generated chunks.

## Testing
<!-- Tick only checks that were run for this PR. -->
- [x] Unit tests pass (`pytest tests/unit/test_structural_chunker.py -m unit`)
- [ ] Integration tests pass (`make test-integration`)
- [ ] Linter passes (`make lint`)
- [ ] Type checker passes (`make typecheck`)
- [x] New/updated tests cover the changes (`pytest tests/unit/test_structural_chunker.py -m unit`)

To reproduce the original bug from `main`:

1. Check out `main` and activate the project virtual environment.
2. Run:
	```bash
	python -c 'from ingestion.chunking.structural_chunker import StructuralChunker; print(StructuralChunker().chunk("Plain text without Markdown headings.", {"source": "repro"}))'
	```
3. Observe that the command prints `[]`, even though the input is non-empty.

To verify the fix on this branch:

1. Check out `fix/149-structural-chunker-silently-drops-documents-with-no-headings` and activate the same environment.
2. Run the command above again; it returns one semantic `Chunk` containing the input and its `source` metadata.
3. Run `pytest tests/unit/test_structural_chunker.py -m unit`.
4. Confirm the suite passes, including coverage for plain text, large headingless text, bullet lists, and a hashtag without a heading space.

## Screenshots / Demo
N/A - the observable behavior is in the ingestion pipeline: headingless documents now produce semantic chunks instead of being discarded.

## Notes for Reviewers
Review the semantic fallback path and its metadata behavior; heading-aware documents continue through the existing structural path.
