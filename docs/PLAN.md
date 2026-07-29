## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula #36](https://github.com/ascherj/pathreview/issues/36#issuecomment-4998114258)

### Understand
The root cause of this issue is due to missing description entailing the formula used to score chunks. Because this is just documentation issue, the expectation is to include all necessary details that can help a dev understand the fundamental backbone components and logic concepts underlying them. In actuality, while the RAG description talks about the general process of chunk retrieval and assessment, it fails to describe how the process gets scored in the assessment. 

### Map
I will definitely be revising ARCHITECTURE.md, as that is the source of the issue. I will also be referring to rag/retriever/hybrid.py for understanding what the hybrid retrieval scoring formula is.

### Plan
1. Understanding where in the ARCHITECTURE.md I need to revise and add resolution to the issue
2. Read and understand the hybrid retrieval scoring formula in rag/retriever/hybrid.py
3. Write a cohesive and concise statement about the hybrid retrieval scoring formula in ARCHITECTURE.md
4. Proofread and submit

### Inputs & outputs
As this isn't an issue requiring coding, there's no technical inputs and outputs. Rather, my fix takes in 
a proper understanding of the hybrid retrieval scoring formula to add a clear description of it for the ARCHITECTURE.md. Ultimately, the final output should be a revised RAG description in that documentation markdown file. 

### Risks & unknowns
There are no unknowns as this is a documentation issue. Only possible risks are misinterpretation and vague/misleading technical writeup of the scoring formula.

### Edge cases
There are no edge cases as this is a documentation issue. 