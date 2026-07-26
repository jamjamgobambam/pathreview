## Solution plan

**Issue:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills — https://github.com/ascherj/pathreview/issues/14

### Understand
`SkillExtractor` (`ingestion/parsers/skill_extractor.py`) only does keyword matching over raw text (source code/README), and `RepoAnalyzer._detect_ci` (`ingestion/parsers/repo_analyzer.py:111`) only checks whether a `.github/workflows` path string is present — it never opens or parses the YAML. Because of this:
- No `workflow_parser.py` exists in `ingestion/parsers/` (confirmed in [tests/unit/test_workflow_parser_reproduction.py](tests/unit/test_workflow_parser_reproduction.py)).
- CI/CD is reduced to a boolean (`has_ci`), losing structured signal like which actions are used (`docker/build-push-action`), which jobs run `pytest`, or whether a deploy job exists.
- `SkillExtractor` can only detect "Docker" because the literal word appears in text, not because a build/push step was structurally identified — so skills like "GitHub Actions," "pytest" (as a CI-run test suite), or "Deployment" never get inferred from a real workflow file.

Expected behavior: a `.github/workflows/*.yml` file should be parsed into structured data (triggers, jobs, steps, `uses:` actions, `run:` commands), and that structure should feed into skill inference so signals like "GitHub Actions," "Docker," "pytest," and "Deployment" are detected with real evidence (which job/step they came from), not just substring matches.

### Map
Files expected to be touched:
- `ingestion/parsers/workflow_parser.py` (new) — parses workflow YAML into structured data, following the `BaseParser`/`ParseResult` contract used by `readme_parser.py` and `repo_analyzer.py`.
- `ingestion/parsers/base.py` — reuse `BaseParser`/`ParseResult` as-is; no changes expected.
- `ingestion/parsers/skill_extractor.py` — add a method (e.g. `extract_skills_from_workflow`) that takes the parsed workflow structure and infers skills ("GitHub Actions," specific actions, "pytest," "Deployment") with evidence tied to job/step names, instead of only ever scanning raw text.
- `ingestion/pipeline.py` — add an `ingest_workflow` method mirroring `ingest_readme`/`ingest_repo_metadata`, wiring `WorkflowParser` into the pipeline the same way `ReadmeParser` and `RepoAnalyzer` are wired in `__init__`.
- `tests/unit/test_workflow_parser.py` (new) — unit tests for the parser itself (triggers, jobs, actions, run commands, malformed YAML).
- `tests/unit/test_skill_extractor.py` — extend with cases for workflow-derived skill inference.
- `pyproject.toml` — add `pyyaml` as an explicit dependency (currently only present transitively in `.venv`; not declared as a direct project dependency).

### Plan
1. Add `pyyaml` as an explicit dependency in `pyproject.toml` and confirm `make setup`/existing lockfile picks it up.
2. Build `WorkflowParser(BaseParser)` in `ingestion/parsers/workflow_parser.py`: parse YAML safely (`yaml.safe_load`), extract `on:` triggers, `jobs:` (names, `runs-on`, `needs`), each job's `steps:` (`uses:` actions with pinned versions, `run:` commands), and return this as `ParseResult.metadata` (mirroring the `heading_hierarchy`-style structured metadata pattern in `readme_parser.py`) plus a flattened `text` summary for embedding.
3. Extend `SkillExtractor` with workflow-aware skill inference: map known actions (`docker/build-push-action`, `actions/setup-python`, etc.) and run-command patterns (`pytest`, `npm test`, `terraform apply`) to `SkillDetection` entries with evidence referencing the specific job/step, reusing the existing `SkillDetection` dataclass and confidence-scoring conventions already used for frameworks/tools.
4. Wire `WorkflowParser` into `IngestionPipeline` as `ingest_workflow`, following the existing `ingest_readme` structure (source_id hashing, skip-check, chunk, embed, record).
5. Write/replace tests: add `test_workflow_parser.py` covering parsing correctness and malformed/missing YAML handling; update `test_skill_extractor.py` for workflow-derived skills; update `test_workflow_parser_reproduction.py` (or remove it) once the gap it documents is closed, since its assertions currently pass *because* the bug exists.

### Inputs & outputs
- **Input:** raw `.github/workflows/*.yml` file content (str or bytes), matching how `ReadmeParser.parse` and `RepoAnalyzer.parse` accept content today.
- **Output:** a `ParseResult` with structured metadata (triggers, jobs, actions used, run commands) and a text summary suitable for chunking/embedding, plus a list of `SkillDetection` objects (e.g. "GitHub Actions," "Docker," "pytest," "Deployment") with evidence pointing at the originating job/step.

### Risks & unknowns
- Real-world workflows use YAML anchors, matrix builds, reusable workflows (`uses: org/repo/.github/workflows/x.yml@main`), and composite actions — need to decide how much of this to support in v1 vs. treat as out of scope.
- Malformed/invalid YAML must fail gracefully (raise a clear `ValueError`, consistent with `ReadmeParser`'s bytes/str validation) rather than crashing the ingestion pipeline.
- Unclear whether workflow ingestion should be a new `source_type` in the pipeline/DB or folded into the existing "repo" source type — affects `pipeline.py` and any downstream consumers of `source_type`.
- Mapping from actions/run-commands to skill names will need a maintained lookup table (similar to `FRAMEWORKS`/`TOOLS` in `skill_extractor.py`), which will need to grow over time as new actions become common — need to scope an initial list rather than trying to be exhaustive.

### Edge cases
- Empty or missing `.github/workflows/` directory (no workflow files at all).
- Workflow YAML with no `jobs:` key, or jobs with no `steps:`.
- Steps using only `run:` (no `uses:`), and steps using only `uses:` (no `run:`).
- Multiple workflow files in one repo (e.g. `ci.yml` and `deploy.yml`) — need aggregation rather than only handling a single file.
- Reusable/composite actions and matrix strategies that don't map cleanly to a single "job = one thing" model.
