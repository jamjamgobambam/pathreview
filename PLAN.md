# Solution plan

**Issue:** [#28 — Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack](https://github.com/ascherj/pathreview/issues/28)

### Understand

When a user's portfolio has multiple projects built with the same tech stack (e.g. three Python projects), the review generator writes a near-identical "Python skills" paragraph for each project instead of noticing the overlap and consolidating it into one observation. Expected: one consolidated skills observation per shared stack, still calling out genuinely distinct feedback between projects. Actual: one repeated paragraph per project.

Root cause, confirmed via `tests/unit/test_review_generator.py::TestFormatContext::test_same_stack_chunks_are_grouped_not_repeated` (currently `xfail`, proving the bug): `ReviewGenerator._format_context` (`rag/generator/review_generator.py:143-160`) concatenates the top 10 retrieved chunks into independent numbered blocks with no grouping by stack, so the LLM sees N same-language chunks side by side and writes a paragraph per chunk. `ReviewGenerator._consolidate_feedback` (`rag/generator/review_generator.py:188-208`) is not a safety net here — confirmed by `test_noop_when_duplicate_content_has_unique_section_names` — it only dedupes by `section_name`, which is already unique across the 5 fixed section names in `generate_full_review`, so it never touches duplicate content *within* a section.

### Map

Files I expect to touch:

- `rag/generator/review_generator.py` — add chunk-grouping step before `_format_context` builds the prompt string; possibly a new `_group_by_stack` helper.
- `rag/generator/prompt_templates.py` — update `skills_feedback` and `projects_feedback` templates to instruct the model to consolidate observations across projects sharing a stack.
- `rag/generator/output_parser.py` — optional backstop: a lightweight near-duplicate collapse over a section's parsed content, in case prompt changes alone don't fully eliminate repetition.
- `tests/unit/test_review_generator.py` — already created this week with the reproduction tests; will extend with tests for the grouping helper and the mixed-stack / single-project cases.

Not touching: `ingestion/pipeline.py` or `ingestion/parsers/repo_analyzer.py` — the `primary_language` / `tech_stack` metadata this fix depends on is already populated there (`ingestion/pipeline.py:236-237`).

### Plan

1. Add a chunk-grouping helper that buckets `context_chunks` by `metadata.tech_stack` (falling back to `primary_language`, then to "ungrouped" if neither is present) before `_format_context` builds the prompt string, so same-stack chunks are presented together with explicit "these N projects share this stack" framing.
2. Wire that helper into `_format_context`, keeping the existing top-10-chunks limit — grouping happens within that limit, not before it.
3. Update the `skills_feedback` and `projects_feedback` prompt templates (`prompt_templates.py`) to instruct the model: when multiple projects share a stack, produce one consolidated observation referencing all of them, not one per project.
4. Re-run `test_same_stack_chunks_are_grouped_not_repeated` and remove its `xfail` marker once it passes for real; add cases for mixed-stack (no incorrect merging) and single-project (unchanged behavior).
5. If prompt changes alone don't fully eliminate repetition (Tier-3 risk noted below), add the backstop dedup step in `output_parser.py` as defense-in-depth.
6. Run `make check && make test-unit` before opening the PR.

### Inputs & outputs

- **Input:** `context_chunks: list[dict]` from `rag/retriever/vector_store.py` / `rag/retriever/hybrid.py`, each with `metadata` (`source_id`, and for repo chunks, `primary_language` / `tech_stack` per `ingestion/parsers/repo_analyzer.py:92,100`) and a relevance `score`. Also `profile_data` (github username, `projects` list).
- **Output:** Same `FeedbackSection` shape as today (`section_name`, `content`, `confidence`, `suggestions`) — this fix only changes the *content* of `skills_feedback` / `projects_feedback`, not the data contract. No new API calls; this is a pure data-shaping/prompting change using metadata the ingestion pipeline already produces.

### Risks & unknowns

- Not all chunks reaching the generator have `tech_stack`/`primary_language` metadata (e.g. resume or README-parsed chunks aren't repo chunks) — grouping must degrade gracefully to ungrouped behavior for those, not crash on a missing key.
- Grouping by stack must not merge genuinely different feedback (e.g. a Python CLI tool vs. a Python Django API) — consolidation should combine observations, not erase meaningful differences between projects.
- This is a Tier-3 issue (7–10 hr estimate); prompt-level instructions alone may not fully stop an LLM from repeating itself, which is why the backstop dedup step exists as a fallback rather than the primary fix.
- `_format_context` hard-limits to the top 10 chunks (`review_generator.py:154`) — grouping logic has to work within that ceiling, not assume it can see every chunk for a project.

### Edge cases

- A profile with only one project: grouping must be a no-op — single-project output should be unchanged from today's behavior.
- Chunks with missing or empty `tech_stack` (e.g. `[]` or absent key): must fall back to `primary_language`, then to treating the chunk as its own ungrouped bucket, rather than raising a `KeyError`.
- Multiple distinct stacks, no overlap (e.g. one Python project, one React project): no grouping should occur — output should look like today's per-project blocks.
- More than 10 same-stack chunks retrieved: grouping happens after/within the existing top-10 truncation in `_format_context`, so it must not assume it sees the full unfiltered chunk set.
