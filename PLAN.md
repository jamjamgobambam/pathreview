## Solution plan

**Issue:** Add a "feedback tone check" that ensures all generated feedback is
written constructively — https://github.com/ascherj/pathreview/issues/69

### Understand
Generated feedback is never checked for *tone*. Expected: every delivered
feedback section reads constructively (actionable, specific, encouraging).
Actual: nothing classifies tone. `safety/content_filter.py` only regex-matches a
short list of genuinely harmful phrases; a section that is dismissive, vague, or
discouraging (but not "harmful") passes untouched. `_run_safety_checks` in
`core/services/review_service.py:365` even lists "Validate feedback tone and
constructiveness" as a numbered comment — the intent is documented but never
implemented. Root cause: a missing classification-and-regeneration step between
generation and delivery.

### Map
Files I expect to touch:
- `safety/content_filter.py` — add a `ToneClassifier` (LLM prompt → constructive
  vs negative + reason). New logic lives in the safety layer, matching the issue.
- `rag/generator/review_generator.py` — in `generate_full_review` /
  `generate_section`, after generating a section, run the tone check and
  regenerate on failure (with a retry cap).
- `rag/generator/prompt_templates.py` — add the tone-classification prompt.
- `core/services/review_service.py` — wire the real tone check into
  `_run_safety_checks` (replace placeholder comment #2).
- `tests/unit/` — new tests for the classifier and the regenerate loop.

### Plan
1. Add tone-classification prompt template + a `ToneClassifier` in the safety
   layer that returns `(is_constructive: bool, reason: str)` from an LLM call.
2. In `ReviewGenerator`, wrap section generation in a loop: generate → classify
   → if negative, regenerate; stop after `MAX_TONE_RETRIES` (e.g. 2) and fall
   back to the best attempt so delivery never blocks.
3. Wire the classifier result into `_run_safety_checks` so tone is a real gate.
4. Add structured logging (`tone_check_failed`, `tone_regenerated`) mirroring
   existing `structlog` calls.
5. Add unit tests (mock the LLM): constructive passes, negative triggers
   regenerate, retry cap respected.

### Inputs & outputs
- Input: a generated `FeedbackSection.content` string (per section).
- Output: either the same section (passed) or a regenerated one; plus a
  boolean/verdict consumed by `_run_safety_checks`. No schema change to
  `api/schemas/review.py`.

### Risks & unknowns
- Infinite/expensive regeneration — mitigated by `MAX_TONE_RETRIES` cap.
- Extra LLM call per section = latency + token cost; may batch or make optional
  via config in `ReviewConfig`.
- Classifier false-positives could reject good feedback — tune prompt, log
  reason for debugging.
- Unknown: does the LLM client (`openai.OpenAI` in review_generator) get reused
  by the safety layer, or does `ToneClassifier` need its own client? Need to
  check how config/keys are passed.

### Edge cases
- Empty or error-fallback sections (`content="Error generating ..."`) — skip
  tone check, don't loop.
- LLM classifier call itself failing/timing out — fail open (deliver original)
  and log, never crash the review.
- Very short sections / non-English content — ensure prompt handles gracefully.
- All retries exhausted — deliver best attempt, flag in logs.
