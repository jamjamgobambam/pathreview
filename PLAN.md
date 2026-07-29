## Solution plan

**Issue:** [Add a "feedback tone check" that ensures all generated feedback is written constructively (#69)](https://github.com/ascherj/pathreview/issues/69)

### Understand

Root cause: nothing in the feedback generation pipeline classifies tone. `ContentFilter.filter()` (`safety/content_filter.py`) only regex-matches genuinely harmful content — self-harm, hate speech, illegal activity — dismissive, vague, or discouraging tone isn't covered by any of its patterns. `ReviewGenerator.generate_section()` / `generate_full_review()` (`rag/generator/review_generator.py`) pass LLM output straight through `parse_review_output()` with no gate in between.

Expected behavior: after generation, each section is classified as constructive (actionable, specific, encouraging) or not; sections that fail the check are rejected and regenerated before the review reaches the user.

Actual behavior (confirmed in Week 8 reproduction): whatever the LLM produces ships unchanged. Fed deliberately dismissive text through both `ContentFilter.filter()` and a mocked `ReviewGenerator.generate_section()` call — both passed it through byte-for-byte untouched.

### Map

Files expected to touch:
- `safety/content_filter.py` — add tone classification (new method on `ContentFilter`, or a new class following the existing `BiasDetector`-style pattern in `safety/bias_detector.py`)
- `rag/generator/review_generator.py` — call the tone check after a section is generated; add a bounded regenerate-on-fail loop, most likely inside `generate_full_review()`'s per-section loop, near the existing `_add_citations` call
- `rag/generator/prompt_templates.py` — likely need a new prompt template for the tone-classification LLM call (LLM-as-judge), reusing the existing `get_template()` machinery
- `tests/unit/test_content_filter.py` — already has one failing test from Week 8 reproduction; will expand with more cases
- Possibly a new `tests/unit/test_review_generator.py` for the regenerate-on-fail behavior
- Open question: `core/services/review_service.py` — see Risks below

### Plan

1. Add a tone-classification method to `safety/content_filter.py` (or a new `ToneChecker` class) that returns `(is_constructive: bool, reason: str)`, mirroring the existing `BiasDetector.detect_bias()` interface for consistency.
2. Add a prompt template for tone classification (constructive vs. discouraging/vague/dismissive) via `prompt_templates.get_template()`.
3. Hook the check into `ReviewGenerator`: after `generate_section()` produces a section, classify it; on failure, regenerate with a bounded retry count (e.g. max 2 attempts) before falling back to a safe default rather than looping indefinitely.
4. Expand test coverage: more classifier test cases (constructive text not flagged, multiple discouraging phrasings flagged) plus tests for the regenerate-on-fail path, mocking the LLM client to return discouraging text first and constructive text on retry.
5. Confirm with a TA/on Slack whether wiring this into the live pipeline (`core/services/review_service.py`, currently entirely stubbed — see Week 8 JOURNAL note) is in scope for #69, and update this plan based on the answer.

### Inputs & outputs

**Input:** a generated feedback section's text (`FeedbackSection.content`, or the raw LLM output before parsing).

**Output:** `(is_constructive: bool, reason: str)` from the classifier. `ReviewGenerator` uses this to either keep the section or trigger regeneration. End-to-end output of the fixed pipeline: `FeedbackSection` objects whose content has been confirmed — or forced, after bounded retries — to be constructive.

### Risks & unknowns

- Tone classification will likely require a real LLM call (LLM-as-judge). No `OPENROUTER_API_KEY` is configured locally, so exercising the real classifier end-to-end needs a key; tests will mock the LLM client the same way the Week 8 reproduction did.
- Retry/regenerate could add unbounded latency or cost if not capped — needs a max-retry limit and a safe fallback (e.g. a generic neutral message) if all retries still fail the check.
- Unclear whether `core/services/review_service.py`'s stubbed pipeline is in scope for #69. If it's out of scope, the fix could be fully correct but never actually exercised by the running app — worth flagging rather than assuming.
- Prompt-based classification is inherently fuzzy; false positives (flagging honest critical feedback as "discouraging") and false negatives are both possible. Needs a test suite covering varied phrasing, not just the one example from the Week 8 repro.

### Edge cases

- Empty or very short feedback text
- Feedback that's harshly worded but factually accurate — constructive-critical vs. genuinely discouraging is a nuanced line, not a keyword match
- All regeneration attempts still fail the tone check (must degrade gracefully, not loop forever or crash)
- Interaction with `ContentFilter.filter()`'s existing harmful-content redaction — ordering between the two checks matters
- Malformed or unusual LLM output that breaks the classification prompt itself
