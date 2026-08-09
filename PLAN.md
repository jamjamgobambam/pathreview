## Solution Plan

**Issue:** #14 -- Add support for parsing GitHub Actions workflow files to detect CI/CD skills — https://github.com/ascherj/pathreview/issues/14

### Understand
Workflow files are silently skipped. A repository with ten GitHub Actions workflows shows zero DevOps skills in its review. The same issue presents with developer resume review and DevOps skills; they aren't listed. 

**Expected behavior:** When a repository contains `.github/workflows/*.yml` files, the ingestion pipeline should parse them and CI/CD skills (GitHub Actions, Docker, pytest, deployment) should appear in the extracted skill set alongside code-derived skills.

**Root cause:** `SkillExtractor.extract_skills()` calls `_detect_tools()`, which iterates over the `TOOLS` dictionary. While `TOOLS` already contains some DevOps keywords (`docker`, `kubernetes`, `ci/cd`, `jenkins`, `terraform`, `ansible`), it lacks `Github Actions`, `pytest`, and `deployment`.
 
Most critical, no parser in `ingestion/parsers/` implements `BaseParser` for `.yml` workflow files, so workflow text never reaches `extract_skills()` in the first place. The ingestion pipeline iterates over repository files and dispatches to parsers based on file type or extension, but `.github/workflows/*.yml` files are not matched by any existing parser (`ResumeParser` handles PDFs and Markdown, `ReadmeParser` handles READMEs). Workflow YAML text is never extracted, chunked, or passed to `SkillExtractor`, so CI/CD skills remain invisible regardless of what keywords exist in `TOOLS`.

---

### Map

**Files I expect to create:**

`ingestion/parsers/workflow_parser.py` 
- New parser implementing `BaseParser` to read `.github/workflows/*.yml` files and return `ParseResult`.

**Files I expect to modify:**

`ingestion/parsers/skill_extractor.py` 
- `TOOLS` dict (Line 93): Add `github actions (0.90)`, `pytest (0.85)`, `deployment (0.85)`. 
- `_detect_tools()` (Line 263): Verify lowercase substring matching handles new multi-word keywords correctly.

`ingestion/parsers/__init__.py`  
- Register `WorkflowParser` (if parser registration exists; verify during reproduction).

`tests/unit/test_workflow_parser.py`
New unit tests following `test_batch_processor.py` pattern.

**Files to be read (for interface compliance):**
`ingestion/parsers/base.py` 
- Confirm `BaseParser` and `ParseResult` signatures.

`ingestion/parsers/resume_parser.py`
- Reference implementation of `BaseParser`.

`ingestion/parsers/pipeline.py`
- Investigate how parsers are dispatched; confirm whether registration is automatic (via `__init__.py` discovery) or manual (hardcoded list), to determine how WorkflowParser gets invoked.

**Integration point:** 
- The workflow parser must produce `ParseResult` with `source_type="workflow"` so `SkillExtractor` can score it like any other parsed document.

---

### Plan

**Sub-task 1: Verify parser dispatch mechanism**
- Read `ingestion/parsers/__init__.py` and `ingestion/parsers/pipeline.py` to confirm how parsers are registered. If registration is manual, note the exact list or factory where WorkflowParser must be added. If automatic, confirm the discovery pattern (e.g., class name suffix "Parser"). This prevents a working parser that never gets called.

**Sub-task 2: Reproduce the gap locally**
- Create a minimal test repository with a `.github/workflows/ci.yml` file containing `actions/checkout`, `docker/build-push-action`, and `pytest` references. 

- Run the current ingestion pipeline against it and confirm that `SkillExtractor.extract_skills()` returns no CI/CD skills. Commit this reproduction as a failing test or documented script.

**Sub-task 3: Implement `WorkflowParser`**
Create `ingestion/parsers/workflow_parser.py` that:
- Accepts a file path or directory path (not raw bytes/string like `ResumeParser` -- workflow files live on in `.github/workflows/`).
- Uses `pathlib.Path.glob(".github/workflows/*.yml")` to discover files.
- Reads each `.yml` file with `yaml.safe_load()` (add `PyYAML` to `requirements.txt` if absent).
- Extracts relevant strings: job names, step names, action references (`uses:`), and runner images (`runs-on:`).
- Concatenates findings into a single text block.
- Returns `ParseResult(text=concatenated_text, metadata={"file_count": N, "workflow_names": [...]}, source_type="workflow")`.

**Sub-task 4: Wire parser into `SkillExtractor` and expand keyword dictionary**
- Add `github actions`, `pytest`, and `deployment` to `SkillExtractor.TOOLS` with appropriate confidence scores. Verify that passing workflow parser output through `extract_skills()` now yields the expected `SkillDetection` objects.

**Sub-task 5: Write unit tests for `WorkflowParser`**
- Create `tests/unit/test_workflow_parser.py` following the `@pytest.mark.unit` class pattern from `test_batch_processor.py`. Mock filesystem I/O (`pathlib.Path.glob`, `Path.read_text`, `yaml.safe_load`) so tests run without real `.yml` files. Covers single workflow, multiple workflows, empty workflows directory, malformed YAML, and missing `.github/workflows/` directory.

**Sub-task 6: Integration smoke test**
- Run the full ingestion pipeline against the reproduction repository from Sub-task 2 and confirm CI/CD skills now appear in the output. Update `JOURNAL.md` with the reproduction commit link and observed results.

---

### Inputs & Outputs

**Input to the fix:**
- A repository path (string or `Path`) pointing to a local git repository.
- `.github/workflows/*.yml` files inside that repository.

**Output of the fix:**
- `WorkflowParser.parse(repo_path)` -> `ParseResult` with concatenated workflow text + metadata.
- `SkillExtractor.extract_skills()` now detects `gitHub actions`, `Docker`, `pytest`, `deployment` when workflow text is passed in.
- Updated skill set includes CI/CD skills in the final review.

**Test Code:**

def test_parse_finds_workflow_files(self, parser, sample_workflow_dict):
    """Test that parser discovers .github/workflows/*.yml files."""
    mock_file = MagicMock(spec=Path)
    mock_file.name = "ci.yml"
    mock_file.read_text.return_value = "mock yaml content"

    with patch("pathlib.Path.glob", return_value=[mock_file]):
        with patch("yaml.safe_load", return_value=sample_workflow_dict):
            result = parser.parse("/fake/repo")

    assert result.source_type == "workflow"
    assert "actions/checkout" in result.text
    assert "pytest" in result.text.lower()
    assert "docker" in result.text.lower()

---

### Risks & Unknowns

| Risk | Mitigation |
|---|---|
| `BaseParser.parse()` signature expects `str` or `bytes`, but workflow files are discovered via filesystem glob. I may need to override the interface or accept a path string. | Read `base.py` during reproduction to confirm whether `parse()` can accept a path. If not, implement a `parse_from_path()` class method or adjust the call site in the ingestion orchestrator. |
| `PyYAML` may not be in `requirements.txt`. Adding it could conflict with existing YAML handling. | Check `requirements.txt` and `pyproject.toml` during reproduction. If absent, add with a pinned version and test install in the virtual environment. |
| `SkillExtractor` keyword matching is naive (lowercase substring search). `pytest` inside a workflow file might also match `pytest` in a Python test file, causing duplicate or inflated confidence. | This is acceptable — the issue asks for skill detection, not deduplication. Document in edge cases. |
| The ingestion orchestrator may not auto-register new parsers. I may need to manually add `WorkflowParser` to a parser list or factory. | Inspect `ingestion/parsers/__init__.py` and the main ingestion entry point during reproduction. |
| Mocking `yaml.safe_load` in tests requires understanding its return shape (nested dicts). Incorrect mocks could pass tests but fail in production. | Use real `yaml.safe_load` on fixture strings in test setup, or hand-craft nested dicts that match GitHub Actions schema. |

### Edge Cases

- **No `.github/workflows/` directory:** Parser should return `ParseResult` with empty text and `metadata={"file_count": 0}` rather than raising an exception.

- **Empty `.yml` files:** Files with only whitespace or comments should be skipped in concatenation but counted in `file_count`.

- **Malformed YAML:** A file with invalid YAML syntax should be logged as a warning and skipped, not crash the entire parser.

- **Non-workflow `.yml` files in `.github/workflows/`:** Any `.yml` file in the directory is assumed to be a workflow per GitHub convention; no additional filtering needed.

- **Very large workflow files:** Concatenation of many large files could produce a huge text block. Cap individual file text at a reasonable limit (e.g., 10,000 chars) or note it as a future optimization.

- **Workflow files with no detectable skills:** A workflow that only uses generic actions (`actions/checkout`, `actions/setup-python`) with no Docker, pytest, or deployment references should return empty skill detections -- this is correct behavior, not a bug.

---