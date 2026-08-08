## Solution plan

**Issue:** [#28 — Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack](https://github.com/ascherj/pathreview/issues/28)

### Understand

**Expected behavior:** when a user has several projects built with the same technology (e.g. three Python RAG projects), a shared observation should be stated once and attributed to all the projects it applies to — "Strong Python/RAG skills, demonstrated across rag-chatbot-alpha, -beta, and -gamma."

**Actual behavior:** the generator repeats a near-identical observation once per project, so the skills feedback reads as repetitive and padded.

**Root cause (verified in code, and reproduced in `tests/unit/test_review_generator.py`):**

1. `generate_section` in `rag/generator/review_generator.py` flattens every project's chunks into one `{context}` blob via `_format_context` and passes only `project_count` (an integer) to the prompt. The model sees three similar projects side by side with no project boundaries and no instruction to consolidate, so it comments on each independently.
2. The `_consolidate_feedback` safety net is a no-op: its docstring promises to merge feedback about the same project, but it only deduplicates by `section_name` — which `generate_full_review` already guarantees is unique — so it never inspects content. Proven by the xfail tests in the reproduction commit.
3. Structured output is lost before consolidation could use it: `_parse_json_output` in `rag/generator/output_parser.py` fans one response into one section per top-level JSON key, and `generate_section` keeps only `sections[0]`, dropping the rest.

### Map

Files I expect to touch:

- `rag/generator/review_generator.py` — `_format_context`, `generate_section`, `_consolidate_feedback` (the core of both layers of the fix)
- `rag/generator/prompt_templates.py` — add a `v2` `skills_feedback` template with per-project context and an explicit consolidation instruction (templates are already versioned, so `v1` stays untouched)
- `rag/generator/output_parser.py` — preserve the structured per-observation shape (skill + evidence + projects) instead of flattening it, so consolidation has something to operate on
- `tests/unit/test_review_generator.py` — the reproduction tests flip from xfail to passing (strict xfail forces removing the markers); add tests for the new grouping/merging behavior
- `tests/unit/test_prompt_templates.py`, `tests/unit/test_output_parser.py` — extend for the v2 template and parser changes

Read-only context: `ingestion/vector_store` `add_chunks` (persists only `source_id`/`chunk_index`/`section` — `source_id` is the reliable project key) and `agent/orchestrator.py` (first-repo-only `break` limits live multi-project data; out of scope).

### Plan

1. **Make context project-aware (prevention).** In `_format_context`, group retrieved chunks by `metadata.source_id` and emit them under explicit `=== Project: <source_id> ===` headers; build a project inventory list and pass it into the prompt alongside `project_count`.
2. **Add a `v2` skills template.** In `prompt_templates.py`, ask for `key_skills` as a list of `{skill, evidence, projects: [ids]}` and instruct: when a skill applies to multiple projects, emit ONE entry listing all of them. Switch `generate_section` to request `v2` for `skills_feedback`.
3. **Preserve structure in the parser.** Update `output_parser.py` (and the `sections[0]` handling in `generate_section`) so the per-observation structure survives parsing instead of being flattened to a JSON string blob.
4. **Implement real consolidation (cure).** Rewrite `_consolidate_feedback` to merge observations whose normalized skill name matches exactly and union their project lists; keep it a pure function so it stays unit-testable.
5. **Flip the reproduction tests and extend coverage.** Remove the xfail markers, add cases for grouping, merging, and the edge cases below; run `make test-unit` and `make lint`.

If exact-match merging proves too weak against the model's paraphrasing, upgrade to lexical or embedding-based near-duplicate clustering (an embeddings provider already exists in `ingestion/embeddings/provider.py`) — but only if step 2's prompt change doesn't already eliminate most duplication.

### Inputs & outputs

- **Input:** the same retrieved chunks (`{text, score, metadata: {source_id, chunk_index, section}}`) and `profile_data` that the generator receives today — no schema or ingestion changes.
- **Output:** the same `list[FeedbackSection]` contract, but the skills section contains each shared observation once, with an explicit list of the projects it applies to. Downstream consumers (citations, review service, frontend) keep working because the section shape is unchanged.

### Risks & unknowns

- **Parser fan-out is load-bearing:** other sections' templates (e.g. `projects_feedback`) also return multi-key JSON that flows through `_parse_json_output` → `sections[0]`. Changing that path could alter what non-skills sections contain — I need to trace `generate_section`'s consumers in `core/services` before changing the return shape.
- **Prompt compliance is probabilistic:** the model may ignore the consolidation instruction or vary skill names ("Python" vs "Python 3"), which is why the deterministic `_consolidate_feedback` layer exists as a backstop — and why it must not depend on the prompt behaving.
- **Frontend rendering:** the skills section content changes shape (projects list per skill); I haven't yet checked how `frontend/` renders section content — if it renders raw JSON content strings, attribution formatting matters.
- **Pre-existing suite failures:** 53 unit tests fail on this branch before my changes (verified by running the suite with and without my commit); I must not let those mask new regressions — I'll compare failure lists, not just counts.
- **Live verification is constrained:** the orchestrator only ingests the first repo (`break` in `agent/orchestrator.py:100`), so an end-to-end multi-project run needs seeded data rather than a real multi-repo ingest.

### Edge cases

- **Single project** — nothing to consolidate; output must be unchanged (no "applies to: [only-project]" noise).
- **Same stack, genuinely different observations** — three Python projects where the model says something *different* about each must NOT be merged; merging keys on the skill, not the project's tech stack.
- **Chunks missing `source_id`** — `_format_context` currently defaults to `"unknown"`; grouping must tolerate that without inventing an "unknown" project entry in attributions.
- **Non-JSON model output** — the plaintext fallback path (`_parse_plaintext_output`) has no structure to consolidate; the fix must degrade gracefully to today's behavior instead of crashing.
- **Case/whitespace variants of the same skill** — "python" vs "Python " should merge (normalize before matching); "Python" vs "Django" should not.
- **Empty retrieval** — no chunks retrieved; the project inventory is empty and the prompt must still format without KeyErrors.
