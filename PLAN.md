# Solution plan

**Issue:** Generator produces duplicate feedback sections when a user has
multiple projects in the same tech stack —
https://github.com/ascherj/pathreview/issues/28

### Understand

**Root cause.** `ReviewGenerator._consolidate_feedback`
(`rag/generator/review_generator.py`) is meant to merge repeated feedback, but
it deduplicates **by `section_name` only** and never inspects the feedback
content:

```python
seen = set()
for section in sections:
    if section.section_name not in seen:   # name-based dedup only
        consolidated.append(section)
        seen.add(section.section_name)
```

When a user has several projects in the same stack, each project yields a
section with a **distinct name** (e.g. `skills_feedback_flask_api`,
`skills_feedback_data_pipeline`, `skills_feedback_cli_tool`) but **identical or
near-identical content**. Since the names differ, nothing is deduped and every
copy survives.

**Expected vs. actual**
- *Expected:* near-identical observations across same-stack projects are
  consolidated into a single cross-project comment that names the projects it
  applies to.
- *Actual:* one repeated section per project; the review reads as padded and
  repetitive.

Reproduced by `tests/unit/test_issue_28_duplicate_feedback.py` (3 projects →
3 sections after consolidation; expected 1). Currently marked `xfail(strict)`.

### Map

Files/functions involved:

| File | What changes |
|---|---|
| `rag/generator/review_generator.py` | Rewrite `_consolidate_feedback` to group by content similarity and merge; add a small similarity/merge helper. |
| `rag/generator/output_parser.py` | Possibly extend `FeedbackSection` with an optional `projects`/`sources` field so a merged section can record which projects it covers. Also fix the pre-existing dead `sections = []` (line 29) that trips mypy. |
| `tests/unit/test_issue_28_duplicate_feedback.py` | Drop the `xfail` marker and expand into full coverage once fixed. |
| `tests/unit/test_output_parser.py` | Add a case if the `FeedbackSection` shape changes. |

### Plan

1. **Group by content, not name.** In `_consolidate_feedback`, normalize each
   section's content (strip/lowercase, and parse the JSON payload so key order
   doesn't matter) and cluster sections whose observations are equivalent using
   a conservative similarity threshold (`difflib.SequenceMatcher`, ratio ≳ 0.9).
2. **Merge each cluster into one section.** Keep the first section as the
   representative, record the set of projects/section names it applies to, and
   union the `suggestions` (de-duplicated). Non-duplicate sections pass through
   untouched and in original order.
3. **Represent the cross-project scope.** Prefer adding an optional
   `projects: list[str]` field to `FeedbackSection` (defaulted, so existing
   callers are unaffected); fall back to a content prefix like
   "Across flask_api, data_pipeline, cli_tool: …" if changing the dataclass
   proves too invasive.
4. **Fix the reproduction test.** Remove the `xfail(strict)` marker so the test
   now asserts the fix, and add edge-case tests (below).
5. **Clean up the pre-existing mypy error** in `output_parser.py` so the
   pre-commit `mypy` hook and CI pass on any commit touching these files.

### Inputs & outputs

- **Input:** `list[FeedbackSection]` produced by `parse_review_output`, possibly
  containing several sections with identical/near-identical content that
  correspond to different same-stack projects.
- **Output:** `list[FeedbackSection]` in which equivalent cross-project
  observations are collapsed into a single section that (a) references all
  affected projects and (b) carries the union of their suggestions. Distinct
  feedback is preserved unchanged; ordering is stable.

### Risks & unknowns

- **Similarity threshold tuning.** Too aggressive merges genuinely distinct
  feedback; too lax leaves duplicates. Mitigation: conservative default +
  tests that assert distinct feedback is preserved.
- **Content is JSON-serialized.** `_parse_json_output` stores
  `content=json.dumps(value)`; comparing raw strings is brittle if key order
  differs. Mitigation: parse/normalize before comparing.
- **Changing `FeedbackSection`.** Adding a field could ripple into
  `_add_citations`, the API review schema, and existing tests. Mitigation: make
  the field optional with a default; grep all constructors/consumers first.
- **No end-to-end path yet.** `_run_rag_retrieval_generation` in
  `core/services/review_service.py` is still a placeholder, so the real LLM
  generate path isn't wired up; correctness will be validated via unit tests
  rather than a live review.
- **Pre-existing mypy debt** in `output_parser.py` (dead `sections = []`) must
  be resolved for hooks/CI to go green.

### Edge cases

- Empty list → empty list.
- Single section → returned unchanged.
- All sections identical → collapse to one (listing every project).
- Mix of duplicates and unique feedback → duplicates merged, uniques preserved.
- **Same `section_name`, different content** → must NOT be dropped (the current
  code silently loses the later one — a latent data-loss bug to fix alongside).
- Near-identical but semantically different content near the threshold boundary.
- Plain-text/`general_feedback` fallback sections (non-JSON content).
