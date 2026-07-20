## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/149)]

**Issue title:** [Structural chunker silently drops documents that contain no headings]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[During the ingestion phase of the RAG system, if a markdown file does not properly have its headers, then the document will fail to be chunked. Due to this being related to the ingestion part of the program, the issue is likely going to be found in ingestion/chunking/structural_chunking.py as that is the most relevant part of the program. If that is not the case, it will at least be a strong point to start the investigation. A successful fix to this issue will allow for markdown files without headers to be properly chunked by utilizing some other strategy that does not rely on headers.]

**Branch name:** [fix/149-chunker-drops-docs-with-noheading]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger