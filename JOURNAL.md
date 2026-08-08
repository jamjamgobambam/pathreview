## Pathreview: Choose Your Issue

## Issue Selected
- Issue #28: Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/28

**Issue title:** Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack

**Tier:** [ ] Tier 1  [ ] Tier 2  [✅] Tier 3

**Problem summary:**
The generator produces nearly identical "skills" feedback for each project when a user has several projects built with the same technology — for example, three Python RAG projects. Instead of recognizing that the observation is shared and giving one consolidated piece of feedback, it repeats similar feedback for each project, so the review reads as repetitive and padded. A successful fix would make the generator deduplicate and consolidate these cross-project observations — stating a shared skill once and attributing it to all the projects it applies to — so the review feels distinct rather than repetitive. The affected code lives in `rag/generator/review_generator.py` and `rag/generator/output_parser.py`.

**Branch name:** fix/28-generator-duplicates

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Is This Issue Right for Me?
I selected this as a Tier 3 (advanced / AI-system) issue, and I'm comfortable taking it on: I was able to trace the root cause in the codebase before starting, so I know where the fix lives. The scope is well-bounded — the change is contained to two files in the RAG generation layer (`review_generator.py` and `output_parser.py`) rather than rippling across the app — and the core defect is already identified: a `_consolidate_feedback` method that never actually consolidates. The estimated effort (~7–10 hours per the issue) fits the Module 3 timeline. There is one other person working on this issue, but I will be able to implement, test, and submit a PR by the Week 9 deadline, and I don't see any blockers.

## Design Note — Deduplicating cross-project feedback

**Goal (per the issue):** deduplicate and *consolidate* cross-project
observations — say a shared skill once, attributed to all the projects it
spans — rather than generating distinct per-project feedback. Consolidation,
not differentiation.

**Why it happens today.** Reviews are generated per *section*
(`skills_feedback`, `projects_feedback`, …) in `generate_full_review`, not
per project. `generate_section` flattens every project's chunks into one
`{context}` blob and passes only `project_count` (an integer) and
`github_username` to the prompt. The model sees three similar Python projects
side by side, with no project boundaries and no instruction to consolidate,
so it comments on each independently. The existing `_consolidate_feedback`
method is a no-op: its docstring promises to "merge feedback for the same
project," but it only deduplicates by `section_name` (which is already
unique), so it never inspects content or projects.

**What identifiers are available.** At generation time each chunk's metadata
carries only `source_id`, `chunk_index`, and `section` — the richer
per-project metadata (`primary_language`, `repo_name`, `tech_stack`) computed
in `repo_analyzer.py` is dropped by `vector_store.add_chunks`. So `source_id`
is the reliable project key to group on.

**Approach — prevention plus cure, across the two files:**

Layer 1 (prevention, `review_generator.py`): make the generator
project-aware. Group retrieved chunks by `source_id` in `_format_context`,
emit them under explicit `=== Project: <source_id> ===` headers, and pass a
project inventory into the prompt. Update the `skills_feedback` template so
each observation is tagged with the projects it applies to
(`key_skills: list of { skill, evidence, projects: [ids] }`) and instruct the
model: when a skill applies to multiple projects, emit ONE entry listing all
of them instead of repeating it per project. This removes most repetition at
the source.

Layer 2 (cure, `review_generator.py` + `output_parser.py`): implement a real
`_consolidate_feedback` as a post-processing safety net that merges
observations describing the same skill and unions their project lists. This
needs structured input, which is currently blocked in the parser:
`_parse_json_output` fans one response out into one section per top-level JSON
key, and `generate_section` then keeps only `sections[0]`, dropping the rest.
So `output_parser.py` must preserve the structured per-observation shape
(skill + evidence + projects) for consolidation to operate on. Start with
normalized exact-match merging on the skill name; upgrade to lexical or
embedding-based near-duplicate clustering (an embeddings provider already
exists in `ingestion/embeddings/provider.py`) only if the model still varies
its phrasing.

**Caveats to note, not fix here:** the orchestrator only analyzes the first
repo (`break  # Only process first repo for now` in `_build_plan`), and
`add_chunks` persists only `source_id`/`chunk_index`/`section` — both limit
how much per-project signal reaches the generator, but neither blocks this
work.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aishadeveloper/pathreview/commit/5897c749a237e0901142e35673ca3ae377b990a1

**Reproduction summary:**
I reproduced the issue deterministically with unit tests in
`tests/unit/test_review_generator.py`: two `xfail(strict=True)` tests feed
`_consolidate_feedback` (and, via a mocked LLM client, `generate_full_review`)
near-identical skill observations attributed to three same-stack projects and
assert they get consolidated — both fail today, and a passing characterization
test confirms `_consolidate_feedback` returns its input unchanged because it
only deduplicates by `section_name`, which is already unique per section.

**PLAN.md link:** https://github.com/aishadeveloper/pathreview/blob/fix/28-generator-duplicates/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
- 53 unit tests fail on this branch *before* my changes (verified by running
  the suite with and without my commit — same 53 either way, e.g.
  `test_json_array_fallback`, `test_tech_detector` exclusions). I'll diff
  failure lists rather than counts in Week 9 so they don't mask regressions.
- Before changing the parser's return shape I need to trace who consumes
  `generate_section`'s output in `core/services` — the `sections[0]`
  truncation might be load-bearing for non-skills sections.
- A live end-to-end multi-project reproduction is limited by the
  orchestrator's first-repo-only `break`; if I record the walkthrough against
  the running app I'll need seeded multi-project data.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
PLAN.md sub-tasks 1–3 are implemented: `_format_context` now groups chunks
under `=== Project: <id> ===` headers with a project inventory passed to the
prompt, a `v2` `skills_feedback` template instructs the model to emit one
entry per skill with a `projects` list, and `parse_section_output` preserves
the full structured payload that the old `sections[0]` fan-out was dropping.
Confirmed before starting that `core/services` never calls `ReviewGenerator`
(its RAG step is a placeholder), which retired the biggest risk in PLAN.md.

**Next steps:**
Implement the real `_consolidate_feedback` merge (sub-task 4), flip the Week 8
xfail reproduction tests and add edge-case coverage (sub-task 5), then
self-review against docs/CONTRIBUTING.md and open the PR.

**Blockers:**
The repo's pre-commit mypy hook (`disallow_untyped_defs`) checks whole files,
so extending the legacy test files requires annotating their existing
untyped methods — mechanical but it inflates the diff slightly.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/573

**Branch:** `fix/28-generator-duplicates`

**What you built:**
A two-layer fix for issue #28: the skills prompt now sees explicit project
boundaries and a consolidation instruction (prevention), and
`_consolidate_feedback` genuinely merges `key_skills` entries whose
normalized skill names match, unioning their project lists (cure). A shared
skill is now stated once and attributed to every project that demonstrates
it, instead of being repeated per project.

**Tests added or updated:**
`tests/unit/test_review_generator.py` (Week 8's xfail reproduction tests now
pass with markers removed, plus new coverage for project grouping, merge
normalization, different-observations-not-merged, single-project no-op, and
plaintext fallback), `tests/unit/test_output_parser.py` (new
`parse_section_output` suite), `tests/unit/test_prompt_templates.py` (v2
template and version selection). Unit suite: 396 passed; the 53 pre-existing
failures are byte-identical before and after my changes (failure lists
diffed, not counted).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both in the documented sense for this codebase: repo-wide pre-existing
failures exist and are listed in the PR; my changes introduce no new
failures, and all touched files pass ruff, black, and mypy.)

**Draft PR feedback received from:** Shawn Blackman (instructor, @sh4wnbk) —
reviewed the PR on GitHub, pulled the branch and ran the suite locally;
nothing blocking ("Really clean fix"). Also requested review from an AI
mentor. Gave peer reviews to PRs #183 and #182 (issue #34).

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
One review came in, from the instructor Shawn Blackman (@sh4wnbk) on
https://github.com/ascherj/pathreview/pull/573. It was an approval with no
requested changes. He called out the merge logic specifically — that
`_merge_duplicate_skills` normalizes skill names with `casefold()` plus
whitespace collapsing so "Python " and "python" don't read as two different
skills, that project lists are unioned in order without duplicates, and that
it handles both the v2 `projects` list and the legacy singular `project` key.
He also approved of the JSON parse falling through to returning the section
unchanged as a safe default, and noted the value of testing both
`_consolidate_feedback` directly and the end-to-end path through
`generate_full_review`. He pulled the branch and ran the tests locally (13
passed), and disclosed that he used Claude while reviewing. He also requested
a review from an AI mentor; that one hasn't arrived, and no other reviewer or
maintainer has commented as of the Week 10 deadline. The PR is still open and
unmerged, which is expected for this course.

**How you responded:**
Nothing was blocking and no changes were requested, so I made no further code
changes — I didn't want to churn the diff for its own sake after it had been
reviewed and run clean. My reply on the PR thanks him and flags the one thing
his review didn't touch that I still consider open: `_consolidate_feedback`
merges on exact normalized skill names, so it won't catch genuine paraphrases
("Python" vs "Python 3", "RAG pipelines" vs "retrieval-augmented generation").
PLAN.md names embedding-based clustering as the upgrade path if the prompt
layer isn't enough, and I said I'd rather leave that as a documented follow-up
than land speculative complexity in a bug-fix PR. If the AI mentor review
lands after the deadline I'll respond to it on the PR the same way.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the fix — it was establishing what "passing" even
meant in this repo. 53 unit tests fail on this branch before I touch anything,
so "the suite is red" carried no signal. I had to run the suite with and
without my commit and diff the *failure lists*, not the counts, to prove I
hadn't regressed anything; a count comparison would have silently hidden a
swap of one failure for another. The second surprise was scope creep from
below: I went in expecting to rewrite one no-op method, `_consolidate_feedback`,
and found it couldn't be written at all until the parser stopped destroying
the data it needed — `_parse_json_output` fanned one response into one section
per JSON key and `generate_section` kept only `sections[0]`. So a one-method
bug became a three-file change across `review_generator.py`,
`output_parser.py`, and `prompt_templates.py`. Third, the repo's pre-commit
mypy hook runs `disallow_untyped_defs` on whole files, so adding tests to
legacy test modules meant annotating their existing untyped methods first —
mechanical, but it padded the diff in a way I had to explain in the PR.

**What did you learn about working in a large codebase?**
The main shift is that most of what you read, you don't get to change. I spent
real time in `ingestion/vector_store` and `agent/orchestrator.py` and came away
with two constraints I had to design *around* rather than fix: `add_chunks`
persists only `source_id`/`chunk_index`/`section`, dropping the richer
`primary_language`/`tech_stack` metadata that `repo_analyzer.py` computes,
which is why `source_id` became my project key; and the orchestrator has a
`break  # Only process first repo for now`, which is why I couldn't do a live
end-to-end multi-project reproduction and reproduced in unit tests instead. In
my own projects I'd have "just fixed" both and blown the scope of the PR. I
also learned to check consumers before changing a return shape — I'd carried
"the `sections[0]` truncation might be load-bearing" as the top risk in
PLAN.md since Week 8, and it dissolved in ten minutes in Week 9 once I actually
traced it and found `core/services` never calls `ReviewGenerator` at all (its
RAG step is still a placeholder). And the codebase's own conventions did work
for me: prompt templates were already versioned, so adding a `v2`
`skills_feedback` template let me change model behavior without touching `v1`
or anything depending on it.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and for mechanical volume: tracing which
modules call `generate_section`, mapping how a chunk flows from
`vector_store` into `_format_context`, and grinding out the mypy annotations
on the legacy test files. It was also good at expanding an edge case I'd named
into a real test — the "same stack, genuinely different observations must not
merge" case is the one I most wanted covered and least wanted to hand-write.
Where it fell short was judgment about *how much* to build. Asked how to
deduplicate near-identical skills, the natural answer is semantic similarity —
embed the skill names and cluster — and the repo even has an embeddings
provider sitting in `ingestion/embeddings/provider.py` to make that easy. That
would have been the wrong PR: nondeterministic, slow, hard to unit test, and
unjustified until exact-match merging is shown to be insufficient. The
decision to do prevention in the prompt plus a deterministic exact-match cure,
and to write down embeddings as a *conditional* follow-up, was mine. Same for
the small behavioral calls that don't show up in a summary — that a
single-project review must round-trip byte-identically rather than sprouting
an "applies to: [one-project]" annotation, and that chunks with no `source_id`
shouldn't materialize a fake "unknown" project in the attribution list. AI
also couldn't tell me which of the 53 failures were mine; that needed me to
run the baseline.

**What would you do differently if you started over?**
I'd capture the failing-test baseline in Week 7, the day I confirmed setup —
not in Week 8 when I was already writing code and had to backtrack to work out
whether I'd broken things. Second, I'd close open risks instead of carrying
them: the `sections[0]` question sat in PLAN.md for a week and cost me nothing
to answer once I bothered. The frontend rendering risk I listed there I never
did resolve — I still haven't checked how `frontend/` renders a section whose
content is a JSON string with a per-skill `projects` list, and that's the
weakest spot in the PR. Third, I'd record the Week 8 walkthrough video. I
skipped it because the orchestrator's first-repo-only `break` made a live
multi-project demo awkward, but a two-minute screen recording of the xfail
tests failing and then passing would have made the reproduction legible to a
reviewer without them pulling the branch. And I'd write the PR description as
I went rather than reconstructing the pre-existing-failure story at the end.

**What are you most proud of from this module?**
The reproduction, more than the fix. Writing `xfail(strict=True)` tests in
Week 8 that fed three same-stack projects' near-identical skill observations
into `_consolidate_feedback` and asserted consolidation meant the bug was
pinned down as an executable, failing artifact before I wrote a line of the
solution — and `strict=True` meant they couldn't quietly pass for the wrong
reason. Removing those markers in Week 9 and watching them go green is the
cleanest evidence I have that I fixed the thing I claimed to fix, and it's
what the reviewer ended up validating when he ran the suite himself. I also
added a characterization test proving the old method returned its input
unchanged, so the "before" is documented in the repo and not just in this
journal.
