## Solution plan

**Issue:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills — [#14](https://github.com/ascherj/pathreview/issues/14)

### Understand
No parser reads `.github/workflows/*.yml`, so CI/CD skills (GitHub Actions, Docker, pytest, deployment) never get detected — only imports and README text are. `ingestion/parsers/workflow_parser.py` is currently just a placeholder comment.

### Map
- `ingestion/parsers/workflow_parser.py` — implement `WorkflowParser(BaseParser)`
- `ingestion/parsers/skill_extractor.py` — add CI/CD keyword detection (actions used, docker, pytest, deploy)
- `ingestion/pipeline.py` — add `ingest_workflow(...)`, instantiate parser in `__init__`
- `pyproject.toml` — add `PyYAML` dependency (not currently present)
- `tests/unit/test_workflow_parser.py` (new)

### Plan
1. Add `PyYAML` to `pyproject.toml`.
2. Implement `WorkflowParser.parse()`: `yaml.safe_load` the content (str/bytes like `ReadmeParser`), extract triggers, job names, `uses:` actions, `run:` commands into `text` + `metadata` (source_type="workflow", job_count, trigger_events, actions_used). Raise `ValueError` on bad YAML.
3. Extend `SkillExtractor` with a `_detect_ci_cd` step (or new keyword map) so actions/commands map to skills like GitHub Actions, Docker, pytest, Deployment.
4. Wire `WorkflowParser` into `IngestionPipeline` with an `ingest_workflow` method mirroring `ingest_readme`.
5. Add unit tests: valid workflow, multiple jobs, malformed YAML, missing `jobs` key.

### Inputs & outputs
- Input: workflow YAML as `str`/`bytes`.
- Output: `ParseResult(text, metadata, source_type="workflow")` whose text, when run through `SkillExtractor`, yields CI/CD-related `SkillDetection`s.

### Risks & unknowns
- No YAML lib in the project yet — need to add `PyYAML`.
- Overlap with `RepoAnalyzer._detect_ci`'s naive substring check — clarify if this replaces or complements it.
- String-matching heuristics can false-positive (e.g. `run: echo docker`).
- Reusable/composite workflow references (`uses: org/repo/.github/workflows/x.yml@main`) need a safe fallback.
- Unclear if multiple workflow files per repo should be one ingestion call or one per file.

### Edge cases
- Empty/malformed YAML → `ValueError`, not a raw crash.
- Missing or non-dict `jobs`; steps missing both `uses` and `run`.
- `on:` as string, list, or dict (all valid GitHub syntax).
- Non-UTF-8 bytes input (decode with `errors="replace"`).
