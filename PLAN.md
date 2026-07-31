## Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Link:** https://github.com/ascherj/pathreview/issues/36

### Understand
- **Root Cause:** `docs/ARCHITECTURE.md` briefly mentions that the RAG subsystem performs hybrid retrieval combining vector similarity and BM25 keyword search, but it completely omits the mathematical formula, default weights, normalization logic, filtering thresholds, and step-by-step calculation steps. Developers and users inspecting the architecture documentation cannot determine how raw retrieval scores are combined into blended relevance scores or how confidence scores relate to overall evaluation metrics (as observed during initial user testing with score displays).
- **Expected Behavior:** `docs/ARCHITECTURE.md` should include a detailed subsection under the RAG System description that clearly documents:
  1. The mathematical formula for hybrid score blending: `blended_score = (vector_weight * vector_score_norm) + (keyword_weight * keyword_score_norm)`
  2. The default weight parameters (`vector_weight = 0.7`, `keyword_weight = 0.3`).
  3. The score normalization method (`raw_score / max_score` based on the maximum score in each candidate result set).
  4. Minimum score filtering (`min_score = 0.3`) and top-k truncation (`max_chunks = 10`).
  5. A concrete step-by-step worked example showing how candidate document chunks are scored, normalized, blended, filtered, and ranked.
- **Actual Behavior:** `docs/ARCHITECTURE.md` currently contains only a single generic sentence: "Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context from the user's ingested documents." No formula, weights, normalization rules, or examples are provided.

### Map
- `docs/ARCHITECTURE.md`: Primary file to touch. We will add a dedicated `#### Hybrid Retrieval Scoring Formula` subsection within the RAG System description.
- `rag/retriever/hybrid.py`: Reference source of truth implementation (`HybridRetriever` class, `__init__` defaults, `retrieve()` logic, score max-normalization, and score blending equation).
- `JOURNAL.md`: Project log file where reproduction documentation, commit links, and progress notes are tracked.
- `PLAN.md`: Planning framework document detailing solution strategy.

### Plan (Sub-Tasks)
1. **Sub-Task 1: Source Code Analysis & Verification in `rag/retriever/hybrid.py`**:
   - Inspect `rag/retriever/hybrid.py` to verify exact mathematical operations and parameters used in production:
     - Vector weight `vector_weight = 0.7`, Keyword weight `keyword_weight = 0.3`.
     - Normalization: `vector_score_norm = vector_score / vector_scores_max`, `keyword_score_norm = bm25_score / keyword_scores_max`.
     - Blended score equation: `blended_score = (0.7 * vector_score_norm) + (0.3 * keyword_score_norm)`.
     - Threshold filtering (`blended_score >= 0.3`) and top-k sorting (`max_chunks = 10`).
2. **Sub-Task 2: Draft Hybrid Retrieval Scoring Subsection in `docs/ARCHITECTURE.md`**:
   - Add a detailed `#### Hybrid Retrieval Scoring` section under `### RAG System (`rag/`)` in `docs/ARCHITECTURE.md`.
   - Document mathematical formulas, default weight configuration (0.7 vector / 0.3 keyword), max-normalization rules, and filtering criteria.
3. **Sub-Task 3: Construct a Step-by-Step Worked Example**:
   - Detail a concrete numerical walkthrough with 3 sample candidate chunks.
   - Walk step-by-step through raw score retrieval, max score identification, normalization, weighted sum blending, threshold filtering (`min_score = 0.3`), and top-k ranking.
4. **Sub-Task 4: Documentation Review & Verification**:
   - Verify formatting, readability, section headers, and file paths in `docs/ARCHITECTURE.md` and `JOURNAL.md`.

### Inputs & outputs
- **Inputs:**
  - Source implementation logic and parameters in `rag/retriever/hybrid.py` (`vector_weight=0.7`, `keyword_weight=0.3`, max score normalization, `min_score=0.3`, `max_chunks=10`).
  - UX observation notes from `JOURNAL.md` regarding score representation.
- **Outputs:**
  - Updated `docs/ARCHITECTURE.md` with hybrid retrieval formula, score weights, normalization logic, min-score thresholding, and a worked example.
  - Comprehensive `PLAN.md` (and `plan.md`) documenting sub-tasks, inputs/outputs, file-specific risks, and edge cases.
  - Updated `JOURNAL.md` with reproduction summary, PLAN.md link, and file-specific risk analysis.

### Risks & unknowns (Tied to Files)
- **Risks tied to `rag/retriever/hybrid.py`**:
  - Misinterpreting score normalization logic: Code uses max-normalization (`raw_score / max_score`), NOT min-max scaling `(x - min)/(max - min)` or softmax. Documentation must precisely reflect `rag/retriever/hybrid.py`.
  - Missing fallback handling: If maximum raw score is 0, code defaults `max_score` to 1.0 to avoid division by zero. Documentation must accurately describe this zero-division safeguard.
- **Risks tied to `docs/ARCHITECTURE.md`**:
  - Header structure mismatch: Inserting new subsections could disrupt the layout under `### RAG System (rag/)`. Must maintain clean markdown heading hierarchy.
  - Mathematical rendering ambiguity: LaTeX syntax vs standard markdown text rendering. Must use clear, standard markdown formulas readable across environments.
- **Unknowns**:
  - None identified. `rag/retriever/hybrid.py` implementation is fully explicit and deterministic.

### Edge cases
- **Edge Case 1: Chunk present in vector results only**: BM25 keyword score is `0.0`. `keyword_score_norm = 0.0`, so `blended_score = 0.7 * vector_score_norm`.
- **Edge Case 2: Chunk present in keyword results only**: Vector similarity score is `0.0`. `vector_score_norm = 0.0`, so `blended_score = 0.3 * keyword_score_norm`.
- **Edge Case 3: Zero maximum score / Empty result set**: `vector_scores_max` or `keyword_scores_max` is 0; code falls back to `1.0` denominator to prevent division by zero, yielding `0.0` normalized scores.
- **Edge Case 4: Candidate score below threshold**: Chunk with `blended_score < 0.3` is excluded from final retrieved context.