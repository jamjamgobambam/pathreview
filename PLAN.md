## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings #149 

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of this issue is that the content is only collected if a heading is presented. Content is only collected once a heading is on the stack and if there is no heading on the stack, then no content is ever collected. The expected behavior of this should have skipped text before the first heading instead of skipping the entire document. 

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The files, functions, or modules that are involved with the structural_chunker.py file include semantic_chunker.py, pipeline.py, strategy_selector.py, and the function itself _extract_sections() in strucutural_chunker.py. The testing file test_structural_chunker.py is also used to test the function for its correctness. 

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Confirm that the issue exists and that the tests fail before fixing. 
2. Fix the main issue with the content guard within structural_chunker.py. 
3. Fix the mid-loop save so that text before the first heading is not silently dropped and so it becomes its own section. 
4. Verify that test_structural_chunker.py functions correctly using the tests; test_semantic_chunker.py, test_heading_path_format, test_empty_sections_handled, test_heading_not_in_middle_of_content. 

### Inputs & outputs
What does your fix take as input? What should it produce or change?

The fix itself doesn't change the input of the chunker. StructuralChunker still takes a raw document and metadata as its input. The function _extract_sections() should produce list[dict], with each dictionary shaped: {"content":str, "path": list[str], "level":int}. 

### Risks & unknowns
What could go wrong? What are you still unsure about?

The chunker could create empty chunks from blank preamble or it could emit content twice. I am still unsure if the proposed fix is able to handle all of the edge cases. 

### Edge cases
What inputs or states should your fix handle gracefully?

My fix should be able to gracefully handle a completely empty document that has a heading, documents with repeated headings, and documents that start with a heading. Furthermore, it should be able to handle a document that has pre-heading content as just blank lines. 