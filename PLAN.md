## Solution plan

**Issue:** [#14 — Add support for parsing GitHub Actions workflow files to detect CI/CD skills](https://github.com/ascherj/pathreview/issues/14)

### Understand

**Root cause.** The ingestion pipeline infers a developer's skills from imports, README text, and
repository metadata, but it has **no parser for `.github/workflows/*.yml`**. The pipeline only wires
three parsers — `ResumeParser`, `ReadmeParser`, `RepoAnalyzer` (`ingestion/pipeline.py:10-12` and
`:51-53`). As a result, maintaining CI/CD workflows — a genuine DevOps signal (GitHub Actions,
Docker builds, running `pytest` in CI, deploying on merge) — goes completely undetected.

**Secondary gap.** The existing `SkillExtractor` (`ingestion/parsers/skill_extractor.py`) that the
issue points us at is missing the very skills this feature must surface:
- `pytest` and `deployment` are **not defined anywhere** (`FRAMEWORKS` has only `jest`/`mocha`).
- There is no `GitHub Actions` entry — only a generic `TOOLS["github"] = 0.90`, which renders with
  the wrong casing `"Github"` (via `.title()` at `skill_extractor.py:269`).
- `SkillExtractor` is **not currently called by any parser or by the pipeline** — only by its own
  unit test. So "reuse it" also means wiring its output into `ParseResult.metadata`.

**Decision (Week 9, informed by the step-0 baseline).** `SkillExtractor` detection is literal
substring matching and already carries 5 failing tests; `"github actions"` isn't even a literal
substring of a real workflow file. Rather than harden a flaky shared module as a load-bearing
dependency, `WorkflowParser` does its own structural detection (authoritative) and merely *calls*
`extract_skills` for supplementary signal (issue #14 says "reuse", which we satisfy by calling — not
by editing). The `TOOLS`/`FRAMEWORKS`/casing improvements are deferred to a follow-up so this PR stays
single-purpose. See Plan step 1.

**Expected vs. actual.** Expected: feeding a workflow YAML through the pipeline yields inferred
skills such as `GitHub Actions`, `Docker`, `pytest`, and `deployment`. Actual: there is no code path
that reads workflow files at all, so nothing is produced.

### Map

Files the fix will touch (feature work — a later week):

- **NEW** `ingestion/parsers/workflow_parser.py` — `WorkflowParser(BaseParser)` returning a
  `ParseResult`. Closest template to copy is `ingestion/parsers/readme_parser.py` (simple
  `str | bytes` parser); prior art for CI detection is `RepoAnalyzer._detect_ci`
  (`ingestion/parsers/repo_analyzer.py:111-119`, already keys off `.github/workflows`).
- `ingestion/parsers/skill_extractor.py` — **reused, not modified** (see Plan step 1). `WorkflowParser`
  calls `extract_skills(...)` for supplementary signal only; no edits here this PR. **NB:** this is the
  ingestion `SkillExtractor`; there is a separate, unrelated `SkillExtractor(BaseTool)` at
  `agent/tools/skill_extractor.py:10` — do not touch or wire that one.
- `ingestion/pipeline.py` — import + instantiate `WorkflowParser`, and add an `ingest_workflow(...)`
  method mirroring `ingest_readme` (`:126-199`), stamping `source_type="workflow"` and a
  `workflow_` source-id prefix.
- `ingestion/chunking/strategy_selector.py` — add a `"workflow"` branch (`select_chunker`,
  `:14-32`); today `"workflow"` falls through to the semantic default. Structural chunking suits
  YAML better.
- `tests/unit/test_workflow_parser.py` — **already exists** as a failing reproduction (commit
  `6d607ce`); it imports the not-yet-created `WorkflowParser`, so collection fails with
  `ModuleNotFoundError`. Week 9 makes its four tests pass and adds the edge-case tests below. A
  `sample_workflow_yaml` fixture in `tests/conftest.py` is optional — the repro inlines
  `SAMPLE_WORKFLOW_YAML`.
- `pyproject.toml` — declare `pyyaml` in `dependencies` (installed only transitively today) and
  `types-pyyaml` in the `dev` extra (CI runs `mypy` with `disallow_untyped_defs = true`).
- **Reuse:** `ingestion/parsers/base.py` (`BaseParser`, `ParseResult`). `ParseResult` is a dataclass
  with positional fields `(text, metadata, source_type)` (`base.py:4-9`) — construct with keyword args
  so a positional call can't swap `metadata`/`source_type`. `BaseParser` is not a formal ABC; `parse`
  just `raise NotImplementedError` (`base.py:29`), so the subclass simply overrides it.

### Plan

Ordered for Week 9 execution. Commit after each numbered step so progress stays visible
(conventional commits, `ingestion` scope — see "Week 9 execution & submission" below).

0. **Capture a baseline (before any change).** Run `make check` and `make test-unit` and record
   which failures already exist. The only expected failure on this branch is the `test_workflow_parser.py`
   collection error (the repro). Any *other* pre-existing `make check`/test failure must be noted now
   so it can go in the PR's **Notes for Reviewers** — Week 9's bar is "no new failures," not "fix the
   whole codebase."
1. **Skill detection — parser-authoritative, extractor reused (not extended).** Baseline capture
   (step 0) showed `SkillExtractor` does literal case-insensitive substring matching and already ships
   5 failing tests; and `"github actions"` is *not* a literal substring of a real workflow YAML (it
   carries `actions/checkout`, `runs-on`). So `WorkflowParser` **structurally** detects the skills —
   GitHub Actions from the `on:`/`jobs:` structure, Docker/pytest/deployment from `uses:` / `run:` /
   job names — and writes those authoritative labels into `text` and `metadata["skills"]`. It **also
   calls** `SkillExtractor().extract_skills(summary_text)` and stores that result under a separate
   `metadata["extracted_skills"]`, honoring issue #14's "reuse it" directive without making the
   feature depend on it. **Do not edit `skill_extractor.py`** — its detection gaps (substring matching;
   the 5 pre-existing failures, incl. the `test_database_technology_detection` self-referential typo)
   are pre-existing and out of scope; document them in the PR's Notes for Reviewers and, if desired,
   file a follow-up issue. The originally-planned `TOOLS`/`FRAMEWORKS`/casing edits move to that
   follow-up. Google-style docstrings on anything new (CONTRIBUTING.md).
2. **Implement `WorkflowParser.parse(content: str | bytes) -> ParseResult`.** Decode bytes → str;
   `yaml.safe_load`; raise `ValueError` on unsupported types / invalid YAML. Build a human-readable
   `text` summary (triggers from `on:`, job names, `runs-on`, each step's `uses:` / `run:`), then
   call `SkillExtractor().extract_skills(text, filename)`. This returns `list[SkillDetection]`
   (dataclass: `name`, `category`, `confidence`, `evidence: list[str]` — `skill_extractor.py:6-12`),
   **not** strings — pull `.name` off each and comma-join into a scalar string
   (`", ".join(d.name for d in detections)`) for `metadata["skills"]`; never put the objects or the
   `evidence` list into `metadata` (ChromaDB rejects non-scalars — see Risks). Build `ParseResult`
   with keyword args and set `metadata["source_type"] = "workflow"`. Full type annotations — `mypy`
   runs over `ingestion/` with `disallow_untyped_defs = true`, so an untyped def fails `make typecheck`.
3. **Wire into the pipeline.** Import + instantiate in `IngestionPipeline.__init__`; add
   `ingest_workflow(...)`; add the `"workflow"` branch to `StrategySelector.select_chunker`. Note the
   selector receives its key via `chunk()` → `metadata.get("source_type", "unknown")`
   (`strategy_selector.py:45`), so the new branch fires only because step 2 stamps
   `metadata["source_type"] = "workflow"` — keep the two in sync.
4. **Declare `pyyaml`** (and `types-pyyaml` in `dev`) in `pyproject.toml`, then re-`pip install -e ".[dev]"`
   so `types-pyyaml` is present when `make typecheck` runs.
5. **Tests — make the repro green, then extend.** The four tests already in
   `tests/unit/test_workflow_parser.py` (returns `ParseResult`, detects CI/CD skills, bytes input,
   invalid-type `ValueError`) must pass. Add edge-case tests from the Edge cases list — empty /
   whitespace-only, valid-YAML-but-not-a-workflow, `.yaml` vs `.yml`, matrix builds, malformed YAML →
   `ValueError`. **Any new test class or function must carry `@pytest.mark.unit`** (class-level, as
   `TestWorkflowParser` already does) — `make test-unit` runs `-m unit` and silently skips anything
   unmarked. Verify in isolation with `pytest tests/unit/test_workflow_parser.py -v`, then run the
   full `make test-unit`.
6. **Self-review & verify.** Run `make check` (ruff + black + mypy) and `make test-unit` until clean;
   walk `docs/CHECKLIST.md`; read the full diff (`git diff origin/main..HEAD`) and strip any debug
   prints / stray TODOs. Confirm the baseline failures from step 0 are unchanged.
7. **Draft PR → peer review → ready.** Push the branch, open a **draft** PR early, fill every section
   of `.github/PULL_REQUEST_TEMPLATE.md` (`Closes #14` goes in **Issue**, not the title; **Notes for
   Reviewers** lists the step-0 baseline). Request peer/mentor feedback in Slack, address it, then mark
   Ready for Review. Log both JOURNAL check-ins (Wed / Sun).

### Inputs & outputs

- **Input:** the contents of a GitHub Actions workflow file as `str | bytes` (plus an optional
  `filename`).
- **Output:** a `ParseResult` with `source_type="workflow"`, `text` = a readable summary suitable for
  embedding, and `metadata` including `triggers`, `job_count`/job names, `actions_used`, boolean
  flags (`has_docker`, `runs_pytest`, `has_deployment`), the authoritative structural `skills`
  (comma-joined string) and, separately, `extracted_skills` from the reused `SkillExtractor` (see
  Risks for the serialization constraint). Downstream, `ingest_workflow` chunks + embeds this like
  other sources.

### Risks & unknowns

- **ChromaDB metadata must be scalar** (str/int/float/bool). `extract_skills` hands back
  `list[SkillDetection]` objects (each carrying an `evidence: list[str]`), so dumping the list — or any
  `SkillDetection` / its `evidence` — straight into `metadata` breaks `BatchEmbeddingProcessor`
  storage. Serialize `.name` values to a comma-joined string and/or boolean flags. The existing repro
  test resolves *how* skills must surface: it asserts on
  `(result.text + " " + str(result.metadata)).lower()`, so a comma-joined string satisfies both the
  scalar constraint and the test. Because the assert is lowercased-substring, the parser writing the
  literal label `GitHub Actions` into its summary text is what makes `"github actions" in haystack`
  pass — the (deferred) extractor casing fix is irrelevant to the test.
- **`make test-unit` filters on `-m unit`.** Additional tests without `@pytest.mark.unit` are collected
  by a bare `pytest` run but silently skipped by `make test-unit` — an easy way to think tests pass
  when they never ran.
- **`make typecheck` covers `ingestion/`** with `disallow_untyped_defs = true`; the new parser and any
  new test helpers need full annotations or `make check` fails.
- **Baseline (step 0, captured):** unit suite is **53 failed / 375 passed** on a clean branch before
  our change (the repro module was excluded to get past its collection error). All 53 are pre-existing
  and mostly in unrelated modules (`rag`/`agent`/`safety`/services); 5 are in `test_skill_extractor.py`.
  Record this in the PR's Notes for Reviewers; our bar is *no new* failures.
- `SkillExtractor` matching is case-insensitive **substring** matching (confirmed by the baseline:
  it can't infer Docker from a Dockerfile or JS from `require('fs')`) → also false positives (`git`
  inside `github`). This is why the parser does its own structural detection (Plan step 1) rather than
  routing raw YAML through the extractor.
- **YAML 1.1 `on:` boolean-key gotcha.** `yaml.safe_load("on: push")` returns `{True: 'push'}` — PyYAML
  resolves the unquoted `on` key to boolean `True`. The parser must read triggers from *both* the
  `"on"` and `True` keys, or triggers silently vanish on real workflow files.
- `pyyaml` is only a transitive dependency today (pyyaml 6.0.3 present); relying on `import yaml`
  without declaring it is fragile. Also `types-pyyaml` is **not** installed — mypy fails with "Library
  stubs not installed for yaml" until step 4 adds it and re-installs the `dev` extra.
- Shared-file merge surface: `ingestion/pipeline.py` and `ingestion/parsers/skill_extractor.py` are
  common edit targets for other issues.

### Edge cases

- Empty file; whitespace-only file.
- Valid YAML that is **not** a workflow (no `on:` / `jobs:`) → return a `ParseResult` (do not raise);
  emit no skills / empty flags.
- The `on:` → `{True: ...}` boolean-key gotcha above (look up both `"on"` and `True`).
- `.yaml` vs `.yml` extension.
- Matrix builds (`strategy.matrix`), reusable/composite workflows (`uses:` at the job level).
- Multi-document YAML; anchored/aliased YAML.
- Invalid / malformed YAML → raise `ValueError` (consistent with other parsers).
- `bytes` input with UTF-8 characters.
- A workflow with `on:` triggers but zero jobs.

### Week 9 execution & submission

The code above is the deliverable, but the grade also depends on process (per WEEK9.md). Conventions
are already validated against `docs/`:

- **Branch:** `feat/14-github-workflow-parser` — matches CONTRIBUTING.md `<type>/<issue>-<desc>`. Keep
  it rebased on `main` (no merge commits; CHECKLIST §1).
- **Commits:** `<type>(ingestion): <imperative description>` — e.g. `feat(ingestion): add WorkflowParser
  for GitHub Actions files`, `test(ingestion): cover workflow parser edge cases`. One logical change
  per commit; no `wip`/`fix fix`.
- **PR is the primary graded artifact.** Title in conventional-commit form (`feat: …`); fill every
  `.github/PULL_REQUEST_TEMPLATE.md` section substantively (a deleted heading fails, "N/A — reason"
  passes). Model the **Changes** section on the root-cause framing in *Understand* above; **Screenshots
  / Demo** is `N/A` (backend-only) with one line pointing at `test_workflow_parser.py`.
- **Gate before Ready-for-Review:** `make check` and `make test-unit` both pass (Plan step 6), draft PR
  reviewed by a peer/mentor.
- **JOURNAL.md:** Check-in 1 (Wed) with progress vs. these Plan steps; Check-in 2 (Sun) with the PR
  link, tests touched, and self-review boxes. Submit the `/tree/feat/14-github-workflow-parser` branch
  URL via the portal — not a bare repo link.
