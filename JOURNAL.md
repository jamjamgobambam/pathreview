## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/149)]

**Issue title:** [Structural chunker silently drops documents that contain no headings]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[During the ingestion phase of the RAG system, if a markdown file does not properly have its headers, then the document will fail to be chunked. Due to this being related to the ingestion part of the program, the issue is likely going to be found in ingestion/chunking/structural_chunking.py as that is the most relevant part of the program. If that is not the case, it will at least be a strong point to start the investigation. A successful fix to this issue will allow for markdown files without headers to be properly chunked by utilizing some other strategy that does not rely on headers.]

**Branch name:** [fix/149-chunker-drops-docs-with-noheading]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


**Reproducing the Issue** From the home directory:

% python3 -m tests.unit.test_structural_chunker
% pytest tests/unit/test_structural_chunker.py -v

This runs the unit tests for the structural chunker, which from the issue's title seems to be a reasonable starting point. From here, one of the tests is called `test_document_with_no_headings` and fails during the run. We can see that during the test, it generates a string to simulate a markdown file with no headers. The failure comes from the string not being chunked at all, confirming the issue. From the test case, we can see that the only function called outside of regular test functions is chunk(), which is located in /ingestion/chunking/structural_chunker.py

