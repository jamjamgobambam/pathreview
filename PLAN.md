## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings https://github.com/ascherj/pathreview/issues/149

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Both heading_stack and current_section_lines are empty upon the initalization of the loop. When the document has no headings, these can never be updated, so the function will follow the continually failing path and end up returning the initial state of the list of chunks, an empty list. The expected behavior is that the chunker will seperate chunks based on headings, the actual behavior is that the text will be discarded until a heading is found, at which point expected behaviour engages.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

structural_chunker is the only file that appears to be affected. That is the only file that is expected to be touched. The function affected is _extract_sections(). chunk() should also be checked, as it takes the input from _extract_sections()
The test file test_structural_chunker may be involved for adding additiona testing for the issue.
### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Remove the condition of the else statement checking for if a heading was collected. 
2. Remove the heading_stack requirement from the final if condition so that a document without headings or text without headings aren't prevented from being chunked.
3. Change the save previous section part of _extract_sections() to not require a previous heading to prevent inital text without a heading from being chunked.
4. Ensure that sections has a case for when no heading is provided in order to not break that return function.
5. Add unit tests to ensure that the system will not break in a similar way again.
### Inputs & outputs
What does your fix take as input? What should it produce or change?
text:str. It should produce a list of dicts with content, path, and level.
### Risks & unknowns
What could go wrong? What are you still unsure about?
One thing that could go wrong are issues with the formatting. I am unsure of how to ensure that the heading_stack requirements are not broken by the removal of their requirement.
### Edge cases
What inputs or states should your fix handle gracefully?
It should handle multiple lines without a heading gracefully, i.e. by combining them into one chunk instead of chunking each sentence individually.
It should also not have nearly empty chunks with just a heading. It should combine that heading into the next one if no additional lines are found.