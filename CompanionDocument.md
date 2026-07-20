# Companion Document — Issue #28: Duplicate feedback sections for same-stack projects

## Overall plan — step-by-step

1. Reproduce the bug locally: seed/ingest a profile with 3+ Python projects and run `generate_full_review` to confirm the `skills_feedback` / `projects_feedback` content repeats near-identical language per project.
2. Trace where the duplication is introduced. `ReviewGenerator._consolidate_feedback` (`rag/generator/review_generator.py:188-208`) only dedupes by `section_name`, and `section_names` (`review_generator.py:104-110`) is a fixed list of 5 unique names — so that method is currently a no-op. The real duplication happens *inside* a single section's generated content, because `_format_context` (`review_generator.py:143-160`) concatenates the top 10 retrieved chunks without grouping by project or tech stack, so the LLM sees multiple same-language chunks side by side and writes a paragraph per chunk/project.
3. Group retrieved chunks by tech stack/language before building the prompt context. Ingestion already tags repo chunks with `language` and `tech_stack` metadata (`ingestion/pipeline.py:236-237`), so this is available — it's just unused at generation time.
4. Update the prompt template(s) in `rag/generator/prompt_templates.py` (starting with `skills_feedback` and `projects_feedback`) to instruct the model to consolidate observations across projects that share a stack, rather than repeat them per project.
5. As a defense-in-depth backstop (in case the LLM still repeats itself), add a post-processing dedup step in `output_parser.py` or `review_generator.py` that collapses near-duplicate sentences/paragraphs within a single section's content.
6. Add unit tests covering: multiple same-stack projects → one consolidated observation; mixed-stack projects → no incorrect merging; single project → unchanged behavior.
7. Run `make check && make test-unit` before opening the PR.

## (Inputs) Data: What We Have and What We Need

- **Have:** Retrieved context chunks (`list[dict]`) from `rag/retriever/vector_store.py` and `rag/retriever/hybrid.py`, each chunk carrying `metadata` (including `source_id`, and for repo chunks, `language` / `tech_stack` per `ingestion/pipeline.py:236-237`) and a relevance `score`. Also `profile_data` (github username, `projects` list).
- **Need:** Confirmation that `tech_stack`/`language` metadata is reliably populated for *every* repo chunk reaching the generator (some chunks may come from resume/README parsing without that field) — need to check `ingestion/parsers/` output for non-repo sources and handle chunks with missing stack metadata gracefully (fall back to ungrouped behavior rather than crashing).
- **No new external API calls required** — this is a pure data-shaping/prompting fix using metadata already produced by the existing ingestion pipeline.

## (Functions) Transforms and Logic

- **New: chunk grouping.** A helper (likely in `review_generator.py` or a new `rag/generator/context_grouper.py`) that buckets `context_chunks` by `metadata.tech_stack` (or `language` as fallback) before `_format_context` builds the prompt string, so same-stack chunks are presented together with an explicit "these N projects share this stack" framing instead of as N independent blocks.
- **Updated prompt templates.** `skills_feedback` and `projects_feedback` templates get an added instruction: when multiple projects share a stack, produce one consolidated observation referencing all of them rather than one per project.
- **Backstop dedup (optional/defense-in-depth).** A lightweight similarity check (e.g. normalized text overlap) over the sentences/bullets in a generated section's content, collapsing near-duplicates before the section is returned from `generate_section`.

## (Outputs) Visualization — How Results Are Displayed

- No new visualization surface — this issue only affects the *content* of the existing `FeedbackSection.content` (and `suggestions`) that the frontend already renders as review sections. Output remains markdown/JSON-in-text rendered in the existing review dashboard; success is measured by shorter, non-repetitive section content, not a new UI element.

## (Current State) What's implemented / What's Left

**Working today:**
- Section generation pipeline (`generate_full_review` → `generate_section` → LLM call → `parse_review_output`) runs end-to-end and produces 5 sections per review.
- `_consolidate_feedback` exists and runs, but is a no-op against this bug (dedupes by `section_name`, which is already unique).
- Ingestion already attaches `language`/`tech_stack` metadata to repo chunks.

**Yet to be built (1):**
- Chunk grouping by tech stack prior to prompt construction.
- Updated prompt instructions for cross-project consolidation.
- Unit tests reproducing the duplicate-paragraph scenario.

**Still broken (2):**
- Multi-project, same-stack reviews currently produce repeated near-identical paragraphs (the bug as filed) — not yet fixed on this branch.

## Known issues / watch-outs

- Grouping by `tech_stack` must not accidentally merge genuinely distinct feedback (e.g. two Python projects that demonstrate very different skills, like a CLI tool vs. a Django API) — consolidation should combine *observations*, not hide meaningful differences.
- Chunks without stack metadata (e.g. resume text, non-repo sources) must degrade gracefully rather than erroring when the grouping step runs.
- `_format_context` currently hard-limits to the top 10 chunks (`review_generator.py:154`) — grouping logic needs to work within that limit, not assume unlimited chunks per project.
- This is a Tier 3 issue (7–10 hr estimate) — the LLM-prompting change alone may not fully eliminate duplication, hence the backstop dedup step as a fallback.

## What are you building next and why?

Next: reproduce the bug with a local multi-project fixture and instrument `_format_context`'s output to confirm same-stack chunks are indeed being presented as separate, undifferentiated blocks — this validates the root cause (context shaping, not the LLM alone) before investing in the grouping/prompt changes.
