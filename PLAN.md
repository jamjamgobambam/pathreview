## Solution plan

**Issue:** [Add support for parsing GitHub Actions workflow files to detect CI/CD skills](https://github.com/ascherj/pathreview/issues/14)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Currently, the system uses `SkillExtractor` which only checks import statements, file extensions, and basic keywords for languages and frameworks. It does not parse `.github/workflows/*.yml` files to capture CI/CD actions and tools.
Expected behavior: When a `.github/workflows/*.yml` file is encountered, the system should read its content and correctly infer skills like GitHub Actions, Docker, pytest, etc.

### Map
Which files, functions, or modules are involved?
- `ingestion/parsers/workflow_parser.py` (New file)
- `ingestion/parsers/skill_extractor.py` (Update to use `WorkflowParser` or integrate its logic)
- `tests/unit/test_workflow_parser.py` (New file for testing the new parser)
- `tests/unit/test_skill_extractor.py` (Update tests to ensure integration works)

### Plan
What are the steps to fix this issue?
1. Create `ingestion/parsers/workflow_parser.py` with a `WorkflowParser` class that parses YAML content from `.github/workflows/` files.
2. Implement extraction logic in `WorkflowParser` to map common GitHub Actions steps (e.g., `actions/checkout`, `run: pytest`, `run: docker build`) to standard CI/CD skills.
3. Integrate `WorkflowParser` into the main parsing pipeline (likely in `skill_extractor.py` or a coordinator module), routing files with `.github/workflows/` paths to the new parser.
4. Add unit tests in `tests/unit/test_workflow_parser.py` to cover various valid and invalid workflow configurations.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- **Input:** File paths (specifically matching `.github/workflows/*.yml` or `*.yaml`) and their raw YAML content.
- **Output:** A list of `SkillDetection` objects representing the CI/CD technologies used (e.g., "GitHub Actions", "Docker", "pytest") with appropriate categories and confidence scores.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- **Risks:** The YAML parsing might fail if the workflow file is malformed, so we need to handle `yaml.YAMLError` gracefully.
- **Unknowns:** `pyyaml` is currently not in `pyproject.toml`. Should we add it as a dependency, or use a robust regex fallback to detect standard keys (like `uses:`, `run:`)? We will need a predefined mapping dictionary for popular actions (like `actions/setup-python` -> `Python`).

### Edge cases
What inputs or states should your fix handle gracefully?
- Invalid or unparsable YAML files.
- Empty workflow files.
- Workflow files with no relevant CI/CD steps.
- Files named `.yml` but not in the `.github/workflows/` directory (these shouldn't be parsed by this specific parser).
