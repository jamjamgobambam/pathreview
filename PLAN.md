# Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings
Issue: https://github.com/ascherj/pathreview/issues/149

## Understand

The structural chunker assumes that every Markdown document contains one or more headings. When a document has no Markdown headings, the parser returns no sections, causing the chunker to return an empty list. As a result, the ingestion pipeline skips the document entirely, and it is never indexed for retrieval.

**Expected behavior:** Documents without headings should still produce at least one chunk so they can be indexed.

**Actual behavior:** Documents without headings produce zero chunks and are silently dropped.

## Map

Files and components likely involved:

* Structural chunker implementation (where Markdown headings are parsed into chunks)
* Chunk generation logic
* Ingestion pipeline that consumes generated chunks
* Existing tests for the structural chunker

Files I expect to modify:

* The structural chunker source file
* The structural chunker test file
* Possibly the ingestion pipeline if additional handling is needed

## Plan

1. Reproduce the issue locally using a Markdown document that contains no headings.
2. Identify where the chunker returns an empty list when no headings are detected.
3. Add fallback behavior that creates a single chunk containing the full document whenever no headings are found.
4. Add or update automated tests covering documents with no headings.
5. Verify that documents with headings continue to behave exactly as before and that the ingestion pipeline indexes both document types correctly.

## Inputs & outputs

**Input**

* Markdown document with one or more headings.
* Markdown document with no headings.

**Output**

* Documents with headings continue producing structural chunks.
* Documents without headings produce one fallback chunk containing the document contents instead of an empty list.
* The ingestion pipeline indexes both document types successfully.

## Risks & unknowns

* The parser may intentionally return no sections for reasons other than missing headings, so the fallback should only apply to truly heading-less documents.
* The ingestion pipeline may have assumptions about chunk metadata that the fallback chunk must satisfy.
* Existing tests may need updates if they currently expect an empty result.

## Edge cases

* Empty document.
* Document containing only whitespace.
* Document with front matter but no headings.
* Document containing lists, paragraphs, or code blocks but no Markdown headings.
* Document with malformed or incorrectly formatted headings.
* Very large documents without headings that should still be handled safely.
