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

**Expected vs. actual.** Expected: feeding a workflow YAML through the pipeline yields inferred
skills such as `GitHub Actions`, `Docker`, `pytest`, and `deployment`. Actual: there is no code path
that reads workflow files at all, so nothing is produced.

### Map

Files the fix will touch (feature work — a later week):

- **NEW** `ingestion/parsers/workflow_parser.py` — `WorkflowParser(BaseParser)` returning a
  `ParseResult`. Closest template to copy is `ingestion/parsers/readme_parser.py` (simple
  `str | bytes` parser); prior art for CI detection is `RepoAnalyzer._detect_ci`
  (`ingestion/parsers/repo_analyzer.py:111-119`, already keys off `.github/workflows`).
- `ingestion/parsers/skill_extractor.py` — add CI/CD entries to `TOOLS`/`FRAMEWORKS` and fix display
  casing (see Plan step 1).
- `ingestion/pipeline.py` — import + instantiate `WorkflowParser`, and add an `ingest_workflow(...)`
  method mirroring `ingest_readme` (`:126-199`), stamping `source_type="workflow"` and a
  `workflow_` source-id prefix.
- `ingestion/chunking/strategy_selector.py` — add a `"workflow"` branch (`select_chunker`,
  `:14-32`); today `"workflow"` falls through to the semantic default. Structural chunking suits
  YAML better.
- **NEW** `tests/unit/test_workflow_parser.py`; optionally add a `sample_workflow_yaml` fixture to
  `tests/conftest.py`.
- `pyproject.toml` — declare `pyyaml` in `dependencies` (installed only transitively today) and
  `types-pyyaml` in the `dev` extra (CI runs `mypy` with `disallow_untyped_defs = true`).
- **Reuse:** `ingestion/parsers/base.py` (`BaseParser`, `ParseResult`).

### Plan

1. **Extend `SkillExtractor`.** Add `"github actions": 0.9` and `"deployment": 0.8` to `TOOLS`; add
   `"pytest": ("Python", 0.85)` to `FRAMEWORKS`; extend the display-name special-cases
   (`skill_extractor.py:269`) so `github actions` → `"GitHub Actions"` (a bare `.title()` gives the
   wrong `"Github Actions"`).
2. **Implement `WorkflowParser.parse(content: str | bytes) -> ParseResult`.** Decode bytes → str;
   `yaml.safe_load`; raise `ValueError` on unsupported types / invalid YAML. Build a human-readable
   `text` summary (triggers from `on:`, job names, `runs-on`, each step's `uses:` / `run:`), then
   call `SkillExtractor().extract_skills(text, filename)` and thread the results into `metadata`.
3. **Wire into the pipeline.** Import + instantiate in `IngestionPipeline.__init__`; add
   `ingest_workflow(...)`; add the `"workflow"` branch to `StrategySelector.select_chunker`.
4. **Declare `pyyaml`** (and `types-pyyaml` in `dev`) in `pyproject.toml`.
5. **Tests.** Add `tests/unit/test_workflow_parser.py` following `test_readme_parser.py`: `parser`
   fixture, `ParseResult` assertions, bytes + UTF-8 input, empty input, invalid-type `ValueError`,
   and skill-extraction assertions (`GitHub Actions`, `Docker`, `pytest`, `deployment`).

### Inputs & outputs

- **Input:** the contents of a GitHub Actions workflow file as `str | bytes` (plus an optional
  `filename`).
- **Output:** a `ParseResult` with `source_type="workflow"`, `text` = a readable summary suitable for
  embedding, and `metadata` including `triggers`, `job_count`/job names, `actions_used`, boolean
  flags (`has_docker`, `runs_pytest`, `has_deployment`), and the extracted `skills` (see Risks for
  the serialization constraint). Downstream, `ingest_workflow` chunks + embeds this like other
  sources.

### Risks & unknowns

- **ChromaDB metadata must be scalar** (str/int/float/bool). Putting a raw `skills` **list** into
  `metadata` would break `BatchEmbeddingProcessor` storage — serialize to a comma-joined string
  and/or boolean flags. **This is the main open question going into implementation.**
- `SkillExtractor` matching is case-insensitive **substring** matching → false positives (`git`
  inside `github`, `go` inside `go.mod`). Prefer inspecting structured `uses:` / `run:` values in the
  parser rather than dumping raw YAML at the extractor.
- `pyyaml` is only a transitive dependency today; relying on `import yaml` without declaring it is
  fragile and could break in a clean environment.
- Shared-file merge surface: `ingestion/pipeline.py` and `ingestion/parsers/skill_extractor.py` are
  common edit targets for other issues.

### Edge cases

- Empty file; whitespace-only file.
- Valid YAML that is **not** a workflow (no `on:` / `jobs:`).
- `.yaml` vs `.yml` extension.
- Matrix builds (`strategy.matrix`), reusable/composite workflows (`uses:` at the job level).
- Multi-document YAML; anchored/aliased YAML.
- Invalid / malformed YAML → raise `ValueError` (consistent with other parsers).
- `bytes` input with UTF-8 characters.
- A workflow with `on:` triggers but zero jobs.
