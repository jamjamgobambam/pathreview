## Solution plan

**Issue:** Explain hybrid retrieval scoring logic in `docs/ARCHITECTURE.md` — [paste issue link]

### Understand

The RAG System section in `docs/ARCHITECTURE.md` states that the application uses hybrid retrieval by combining vector similarity and BM25 keyword retrieval. However, the documentation does not explain how the two scores are combined.

The expected documentation should include the exact scoring formula, the default vector and keyword weights, definitions of the score components, and a numerical example. Currently, readers cannot determine how the final hybrid ranking score is produced.

### Map

Files and modules involved:

- `docs/ARCHITECTURE.md` — contains the incomplete hybrid retrieval documentation.
- `rag/` — expected location of the hybrid retrieval implementation.
- The retrieval implementation file inside `rag/` — expected to contain the score-combination logic.
- Any configuration or constants file that defines the default vector and BM25 weights.
- Any retrieval tests that verify hybrid ranking behavior.

The primary file expected to change is:

- `docs/ARCHITECTURE.md`

The implementation and test files will be inspected to verify the documentation, but they are not expected to require changes.

### Plan

1. Search the `rag/` directory to locate the function or class that combines vector similarity and BM25 keyword scores.
2. Identify the exact scoring formula, default weights, and any normalization performed before the scores are combined.
3. Check configuration files and retrieval tests to confirm that the documented defaults match the implementation.
4. Add a hybrid retrieval scoring subsection to `docs/ARCHITECTURE.md` that defines the formula and each variable.
5. Add a worked numerical example using the verified default weights and compare the documentation against the implementation.

### Inputs & outputs

The hybrid scoring process takes the following inputs:

- a vector similarity score
- a BM25 keyword score
- a vector score weight
- a keyword score weight

It produces a combined hybrid score used to rank retrieved documents.

The documentation change should produce:

- the exact hybrid scoring formula
- the default vector and keyword weights
- an explanation of score normalization, if used
- definitions of each variable
- a numerical example showing the calculation

### Risks & unknowns

- Vector similarity and BM25 scores may have different numerical ranges and may require normalization.
- The default weights may be defined in a configuration file rather than directly in the retrieval function.
- Users may be able to override the default weights.
- The implementation may convert vector distance into similarity before combining scores.
- Existing tests may reveal scoring behavior that is not currently described in the architecture documentation.

### Edge cases

The documentation should explain or account for:

- a vector score of zero
- a BM25 score of zero
- documents with no keyword matches
- one scoring component having a weight of zero
- custom weights that differ from the defaults
- equal final hybrid scores
- normalized versus unnormalized component scores