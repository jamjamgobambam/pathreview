## Solution plan

**Issue:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Link:** https://github.com/ascherj/pathreview/issues/36

### Understand
- **Root Cause:** `docs/ARCHITECTURE.md` briefly mentions that the RAG subsystem performs hybrid retrieval combining vector similarity and BM25 keyword search, but it completely omits the mathematical formula, default weights, normalization logic, filtering thresholds, and step-by-step calculation steps. Developers and users inspecting the architecture documentation cannot determine how raw retrieval scores are combined into blended relevance scores or how confidence scores relate to overall evaluation metrics (as observed during initial user testing with score displays).
- **Expected Behavior:** `docs/ARCHITECTURE.md` should include a detailed subsection under the RAG System description that clearly documents:
  1. The mathematical formula for hybrid score blending: `blended_score = (vector_weight * vector_score_norm) + (keyword_weight * keyword_score_norm)`
  2. The default weight parameters (`vector_weight = 0.7`, `keyword_weight = 0.3`).
  3. The score normalization method (`raw_score / max_score` based on the maximum score in each candidate result set).
  4. Minimum score filtering (`min_score = 0.3`) and top-k truncation.
  5. A concrete step-by-step worked example showing how candidate document chunks are scored, normalized, blended, filtered, and ranked.
- **Actual Behavior:** `docs/ARCHITECTURE.md` currently contains only a single generic sentence: "Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context from the user's ingested documents." No formula, weights, normalization rules, or examples are provided.

### Map
- `docs/ARCHITECTURE.md`: Primary file to touch. We will add a dedicated `#### Hybrid Retrieval Scoring Formula` subsection within the RAG System description.
- `rag/retriever/hybrid.py`: Reference source of truth implementation (`HybridRetriever` class, `__init__` defaults, `retrieve()` logic, score max-normalization, and score blending equation).
- `JOURNAL.md`: Project log file where reproduction documentation, commit links, and progress notes are tracked.
- `plan.md`: Planning framework document detailing solution strategy.

### Plan
1. **Source Code Analysis & Verification**: Inspect `rag/retriever/hybrid.py` to verify the exact mathematical operations and parameters used in production:
   - Vector weight `vector_weight = 0.7`, Keyword weight `keyword_weight = 0.3`.
   - Normalization: `vector_score_norm = vector_score / vector_scores_max`, `keyword_score_norm = bm25_score / keyword_scores_max`.
   - Blended score equation: `blended_score = (0.7 * vector_score_norm) + (0.3 * keyword_score_norm)`.
   - Threshold filtering (`blended_score >= 0.3`) and top-k sorting (`max_chunks = 10`).
2. **Draft Hybrid Retrieval Scoring Subsection in ARCHITECTURE.md**:
   - Write mathematical formulas in clean, readable markdown format.
   - Explain weight configuration and why vector similarity is prioritized (`0.7`) over keyword matching (`0.3`).
   - Detail max-normalization logic and fallback defaults when max score is 0.
3. **Construct a Step-by-Step Worked Example**:
   - Create a sample scenario with 3 document chunks.
   - Show raw vector cosine similarity scores and raw BM25 keyword scores.
   - Walk through max score determination, normalized score computation, weighted sum calculation, threshold filtering, and final top-k ranking.
4. **Documentation Review & Formatting Verification**:
   - Verify all file links, headings, and readability in `docs/ARCHITECTURE.md`.
   - Ensure consistency with existing section structures in `docs/ARCHITECTURE.md`.

### Inputs & outputs
- **Inputs:** Implementation specifications from `rag/retriever/hybrid.py` (default weights 0.7/0.3, max-normalization logic, `min_score=0.3`, `max_chunks=10`) and selection notes regarding user-facing score representation.
- **Outputs:** Comprehensive documentation added to `docs/ARCHITECTURE.md` explaining the hybrid retrieval scoring model with formulas and a worked example; updated `plan.md` and `JOURNAL.md`.

### Risks & unknowns
- **Risks:**
  - Misrepresenting normalization: confusing max-normalization (`raw_score / max_score`) with standard min-max scaling (`(score - min) / (max - min)`) or softmax. `hybrid.py` specifically divides by `max_score`, which must be stated clearly.
  - Inconsistency between code and documentation if default weights in `hybrid.py` are altered in future code changes without updating docs.
  - Formatting issues if non-standard LaTeX delimiters are used instead of clear plain markdown text.
- **Unknowns:**
  - Behavior when `vector_scores_max` or `keyword_scores_max` is zero or empty set (handled in code via `default=1.0` fallback to avoid division by zero).

### Edge cases
- **Chunk present in vector results only:** BM25 score defaults to `0.0`. Normalized keyword score is `0.0`, so blended score is `0.7 * vector_score_norm`.
- **Chunk present in keyword results only:** Vector score defaults to `0.0`. Normalized vector score is `0.0`, so blended score is `0.3 * keyword_score_norm`.
- **Zero maximum score / Empty candidate list:** Handled by defaulting `vector_scores_max` and `keyword_scores_max` to `1.0`, resulting in `0.0` normalized scores without crashing.
- **Score below threshold:** Chunks with `blended_score < 0.3` are excluded from the returned results.