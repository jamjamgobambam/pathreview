## Solution plan

**Issue:** [Structural chunker silently drops documents that contain no headings
 #149](https://github.com/ascherj/pathreview/issues/149)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

#### Root Cause

[StructuralChunker._extract_sections()](ingestion/chunking/structural_chunker.py) only collects normal text after it has encountered a Markdown heading. For a document with no lines matching # through ######:

    - heading_stack stays empty.
    - current_section_lines stays empty because ordinary lines are not appended.
    - No section is saved at the end because saving also requires a non-empty heading_stack.
    - _extract_sections() returns an empty list.
    - [StructuralChunker.chunk()](ingestion/chunking/structural_chunker.py) iterates over that empty list and returns [].


#### Expected Behavior 

For any non-empty document, StructuralChunker.chunk() should return at least one meaningful Chunk.

    - Documents with Markdown headings should be split by headings and retain heading_path and heading_level metadata.
    - Documents without headings should fall back to semantic chunking, preserving their text and incoming metadata.
    - Long headingless documents may produce multiple sentence-boundary chunks; short headingless documents should normally produce one chunk.


#### Actual Behavior

For a non-empty, headingless Markdown or text document, 
    - StructuralChunker.chunk() returns an empty list. No chunks are sent to the embedding/indexing stage, so the document is silently absent from RAG retrieval results.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

#### Files expected to change

**structural_chunker.py**

    - StructuralChunker.chunk() is the primary fix location.
    - After _extract_sections(text), it should detect an empty section list for non-empty input and delegate to the existing SemanticChunker.
    - StructuralChunker._extract_sections() explains why no-heading documents produce no sections, but it likely does not need to change because it correctly focuses on extracting Markdown structure.


**test_structural_chunker.py**

    - test_document_with_no_headings() already captures the reported failure and should be strengthened to verify returned chunk text and preserved metadata.
    - Add a test for a large headingless document so the semantic fallback is covered when it returns multiple chunks.

#### Files involved but not expected to change

**semantic_chunker.py**

    - Provides the existing fallback behavior. No implementation change should be necessary.

**base.py**

    - Defines the shared Chunk data structure and BaseChunker contract. No change expected.

**strategy_selector.py**

    - Routes README content to StructuralChunker. No change is needed because it already selects the correct strategy.

**pipeline.py**

    - Calls the selected chunker during README ingestion. No change expected; once StructuralChunker returns fallback chunks, the pipeline will index them normally.


### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Reproduce the no-heading failure with the existing focused test:

```
pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings -q
```

    - Confirm that non-empty plain text currently produces an empty chunk list.

2. Update StructuralChunker.chunk() in structural_chunker.py to check whether _extract_sections(text) returned no sections. When the input is non-empty but contains no Markdown headings, delegate to the existing self.semantic_chunker.chunk(text, metadata) fallback.

3. Strengthen test_document_with_no_headings() in test_structural_chunker.py to verify that:

    - At least one Chunk is returned.
    - The returned text contains the original document content.
    - Incoming metadata is preserved.
    - No heading_path or heading_level metadata is invented.

    
4. Add a test for a long headingless document. Verify that semantic fallback returns non-empty chunks and that concatenated chunk content still represents the input, allowing for intentional overlap behavior.

5. Run the focused structural-chunker test module and formatting/linting checks required by the repository:

```
pytest tests/unit/test_structural_chunker.py -q
make lint
```

Then note any failures that were present before the fix separately from the #149 behavior.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

#### Inputs

The fix uses the existing StructuralChunker.chunk(text, metadata) interface:

- text: a Markdown or plain-text document as a string.
- The relevant new case is non-empty text with no Markdown headings matching # through ######.
- metadata: a dictionary supplied by the ingestion pipeline, such as source_type, source_id, profile_id, repository information, or filename.

#### Outputs

The method continues to return list[Chunk], where every Chunk contains:

```
Chunk(
    text="chunk content",
    metadata={...}
)
```

For headingless, non-empty input, the changed behavior should be:

- Return one or more non-empty Chunk objects instead of [].
- Preserve the original text content in those chunks.
- Preserve all incoming metadata.
- Use the existing SemanticChunker to split large documents on sentence boundaries, following its existing chunk-size and overlap rules.
- Avoid adding heading_path or heading_level, because no Markdown heading hierarchy exists.
- For empty or whitespace-only input, behavior remains unchanged:

```
[]
```

### Risks & unknowns
What could go wrong? What are you still unsure about?

**Changed chunk boundaries:** Headingless documents will now be chunked by SemanticChunker, which uses sentence and newline boundaries. Long documents may produce multiple chunks with overlap rather than one literal chunk. This is intended, but tests should assert preserved content and non-empty chunks rather than an exact chunk count.

**Metadata expectations:** Structural chunks normally include heading_path and heading_level. The fallback should preserve incoming metadata but should not add those heading-specific fields. Existing downstream code must tolerate their absence, which is consistent with chunks produced directly by SemanticChunker.

**Mixed-format documents:** A document containing text before its first Markdown heading still has a structural section later, so _extract_sections() returns sections and the fallback will not run. The current implementation drops that pre-heading text. This is a separate edge case from the reported “no headings” bug and should remain out of scope unless the issue explicitly requires preserving introductory text.

**Semantic chunker limitations:** The fallback inherits SemanticChunker’s sentence-splitting behavior. Text with few punctuation marks, unusual bullet characters, or very long unbroken lines may produce less ideal boundaries, but it will still prevent the complete loss of document content.

**Test baseline:** The repository has known unrelated test or tooling failures. Validation should demonstrate that the focused no-heading test changes from failing to passing, then identify unrelated failures separately.

**There are no major design unknowns for this fix:** StructuralChunker already initializes SemanticChunker, so fallback behavior can be added locally without changing the ingestion pipeline or public interfaces.

### Edge cases
What inputs or states should your fix handle gracefully?

**Empty input:** "" should continue returning [].

**Whitespace-only input:** Text containing only spaces, tabs, and newlines should continue returning [].

**Short headingless text:** A non-empty plain-text document should return one non-empty Chunk with the original metadata preserved.

**Long headingless text:** A large plain-text document should use SemanticChunker and return one or more non-empty chunks rather than being dropped.

**Headingless bullet lists or newline-separated text:** Content without # headings, including -, *, •, or  bullet points, should still be retained and chunked.

**Normal Markdown documents:** Documents containing valid # through ###### headings should preserve the current structural behavior, including heading_path and heading_level.

**A heading with no body content:** The existing code should continue to avoid creating empty chunks or crashing.

**Incoming metadata:** Metadata should be copied onto every fallback chunk without mutating the original metadata dictionary. Heading-specific metadata should only exist when actual Markdown headings were found.

**Text beginning with a non-heading # use:** Lines such as #hashtag do not match the required Markdown-heading syntax because they lack a space after #; they should be handled as headingless content rather than dropped.