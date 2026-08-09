# Solution Plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula

Issue Link:
https://github.com/ascherj/pathreview/issues/36

---

## Understand

The architecture documentation explains that the application uses hybrid retrieval with vector similarity and BM25 keyword search, but it does not explain how these retrieval methods are combined to calculate the final retrieval score. This makes it difficult for new contributors to understand the ranking process.

---

## Map

Files to investigate:

- docs/ARCHITECTURE.md
- rag/
- ingestion/

Additional files may be reviewed if the scoring logic is implemented elsewhere.

---

## Plan

1. Locate the implementation of hybrid retrieval.
2. Identify how BM25 and vector similarity scores are calculated.
3. Determine how the final retrieval score is produced.
4. Update ARCHITECTURE.md with a clear explanation of the scoring process.
5. Review the documentation for clarity and accuracy.

---

## Inputs & Outputs

**Input**

Current architecture documentation and retrieval implementation.

**Output**

Updated documentation explaining the hybrid retrieval scoring formula and ranking process.

---

## Risks & Unknowns

The scoring logic may be distributed across multiple files or external libraries, making it necessary to investigate several modules before documenting the implementation.

---

## Edge Cases

- Documentation should remain understandable for new contributors.
- Future changes to the retrieval algorithm should be easy to document.
- Avoid documenting implementation details that are likely to change frequently.