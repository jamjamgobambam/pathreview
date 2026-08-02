## Solution plan

**Issue:** Add a "feedback tone check" that ensures all generated feedback is written constructively (#69)
https://github.com/ascherj/pathreview/issues/69

### Understand
Currently, `ReviewGenerator.generate_section()` in `rag/generator/review_generator.py` calls the LLM and returns the parsed feedback section directly, with no tone validation. `ContentFilter.filter()` in `safety/content_filter.py` only catches explicitly harmful content (self-harm, slurs, illegal activity) via regex, it has no concept of "constructive vs discouraging" tone, and it's never even called from the review generation flow. Expected behavior: every feedback section shown to a user should be constructive (actionable, specific, encouraging). Actual behavior: harsh or discouraging feedback can be generated and returned with zero checks, confirmed by the reproduction test in tests/unit/test_content_filter.py.

### Map
- `rag/generator/review_generator.py`: `generate_section()` and `generate_full_review()`, where the tone check needs to be called after generation
- `safety/content_filter.py`: where a new `ToneChecker` class will live alongside `ContentFilter`
- `tests/unit/test_content_filter.py`: where reproduction and future tests live

### Plan
1. Add a `ToneChecker` class in `safety/content_filter.py` that uses an LLM prompt to classify feedback as constructive or negative
2. Wire `ToneChecker` into `ReviewGenerator.generate_section()` so every generated section gets checked before being returned
3. If a section fails the check, regenerate it (retry the LLM call once or twice) instead of returning it as-is
4. Add logging (using the existing `structlog` logger) when a section fails and gets regenerated
5. Add unit tests covering both constructive and negative example feedback

### Inputs & outputs
Input: a generated `FeedbackSection` (or raw text) from the LLM. Output: either the same section (if it passes the tone check) or a regenerated section that passes.

### Risks & unknowns
- Adding another LLM call per section increases latency and cost, need to confirm this is acceptable
- Risk of infinite retry loops if regenerated content keeps failing the tone check, need a max retry limit
- Unsure how strict the tone classifier prompt should be, too strict could over-reject valid critical feedback

### Edge cases
- Feedback that's short/empty (edge case where there's little to classify)
- Feedback that's constructive but still contains critical points, must not falsely flag as negative
- Repeated regeneration failures (need fallback behavior, e.g. use last attempt with a warning flag rather than looping forever)