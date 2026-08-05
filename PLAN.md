## ANALYSIS: The Actual Flow from Resume/Github Username Submission to Results

- When a user submits resume + github_username and sees results, those results are **hardcoded placeholders**, not actual outputs from the ingestion pipeline.

- When you query `GET /reviews/{review_id}`, the review exists with valid-looking sections because:
    1. The hardcoded dicts are properly structured (match FeedbackSection schema)
    2. Safety checks validate only structure, not content (see `_run_safety_checks()` line 357)
    3. The DB stores whatever is in `review.sections`, real or hardcoded
    4. The API returns it as-is

- **Request Path:**
    ```
    POST /reviews (reviews.py:22)
    ↓
    FastAPI BackgroundTasks.add_task(process_review, db, review.id, profile_id)
    ↓ (async, returns immediately to client with status="pending")
    process_review() runs in background (review_service.py:82)
    ```

- **Background Processing (What Actually Executes)**:
    - 1. Resume data is NOT parsed or ingested. Instead of calling `IngestionPipeline.ingest_resume()` or `IngestionPipeline.ingest_repo_metadata()`, the code just builds a raw dict (review_service.py:254-270):
        ```python
        if profile.resume_text: 
            resume_data = {
                "source_type": "resume",
                "filename": profile.resume_filename,
                "data": profile.resume_text,  # ← just raw text, never chunked/embedded
            }
            sources.append(resume_data)
            
            # Stores it in IngestedSource table but never calls the pipeline
            ingested = IngestedSource(
                profile_id=profile.id,
                source_type="resume",
                raw_data=json.dumps(resume_data),
            )
            db.add(ingested)
        ```
        - The entire ingestion pipeline infrastructure exists (chunking, embedding, vector storage in ChromaDB) but is **never instantiated or called from review_service.py**. The raw resume text is stored in the DB but never processed through `IngestionPipeline.ingest_resume()` or `IngestionPipeline.ingest_repo_metadata()`.

    - 2. After collecting raw dicts, the code calls functions that return hardcoded placeholder output as results (review_service.py:282-354):
        ```python
        # _run_agent_orchestration() (line 282) returns:
        return {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Analysis of technical skills from ingested sources",  # ← HARDCODED
                    "confidence": 0.8,
                    "suggestions": ["Add more detail on AI/ML experience"],
                },
                {
                    "section_name": "Project Experience",
                    "content": "Analysis of project experience",
                    "confidence": 0.75,
                    "suggestions": ["Include measurable impact metrics"],
                },
            ],
            "overall_score": 0.75,
        }

        # _run_rag_retrieval_generation() (line 307) also returns hardcoded dict
        # with enhanced but still placeholder feedback
        ```

        - Neither function actually:
            - Queries the vector DB (ChromaDB)
            - Retrieves context based on the resume
            - Uses an LLM to generate personalized feedback
            - Reads from the ingestion results at all

    - 3. Results are stored (review_service.py:168-170):
        ```python
        review.status = "complete"
        review.sections = [s.model_dump() for s in sections]  # ← the hardcoded feedback
        review.overall_score = rag_output.get("overall_score", None)  # ← always 0.81
        ```


- **To fix this gap (required for Issue #14):**
    1. Instantiate `IngestionPipeline` inside `_run_ingestion_pipeline()` with real embedding provider + vector DB
    2. Call `pipeline.ingest_resume()`, `pipeline.ingest_readme()`, `pipeline.ingest_repo_metadata()` for each source
    3. Update `_run_agent_orchestration()` and `_run_rag_retrieval_generation()` to query the vector DB instead of returning hardcoded dicts

---

## ANALYSIS: the ideal function flow when a GHA workflow file is encountered

There is **no route** that accepts workflow files submissions. Instead, workflow files are touched indirectly during repo metadata ingestion. Here's the chain:

- **1. Profile creation** (api/routes/profiles.py:23): User submits a GitHub username. The endpoint stores it in `profile.github_username`.
- **2. Review requested** (api/routes/reviews.py:22): `create_review_endpoint()` registers `process_review` function as a `BackgroundTask`.
- **3. Ingestion stub runs** (core/services/review_service.py:197): `process_review()` calls `_run_ingestion_pipeline(db, profile)` to run the ingestion pipeline, which checks `profile.github_username` and builds a raw dict:
    ```python
    # Placeholder: actual GitHub ingestion logic
    github_data = {
        "source_type": "github",
        "username": profile.github_username,
        "data": f"GitHub profile data for {profile.github_username}",
    }
    ```
    - **Note:** Currently, no GitHub API call is made, no repo files are fetched, no workflow YAMLs are read. These data should be fetched and ingested into the `data` field in this dictionary.
    - If `_run_ingestion_pipeline()` is properly wired, it would instead:
        - Use a GitHub API client to fetch actual repo metadata for `profile.github_username`
        - Instantiate IngestionPipeline with a vector DB, DB session, and embedding provider
        - Call `IngestionPipeline.ingest_resume()` (currently it just builds a plain dict from profile.resume_text). Alternatively, you could make it call eagerly at profile creation in api/routes/profiles.py:84 right after the file is uploaded.
        - Call `IngestionPipeline.ingest_repo_metadata(profile_id, repo_data)` for each repo
- **4. Repo metadata path (if wired)** (ingestion/pipeline.py:201): `IngestionPipeline.ingest_repo_metadata()` calls 
    - `RepoAnalyzer.parse(repo_data)`: Analyze repository
    - `StrategySelector.chunk(text, metadata)`: Chunk the content
        - this calls `select_chunker(source_type)` in ingestion/chunking/strategy_selector.py. 
        - right now, select_chunker() only knows "resume", "readme", and "repo" source type
            ```python
            if source_type == "resume":
                return self.semantic_chunker
            elif source_type == "readme":
                return self.structural_chunker
            elif source_type == "repo":
                return self.semantic_chunker
            else:
                # Default to semantic chunking
                return self.semantic_chunker
            ```
        - We may add `"workflow"` as a new source type and select structural_chunker/semantic_chunker for it. Otherwise, it would fall through to the default semantic chunker
    - `BatchEmbeddingProcessor.process(chunks)`: Generate embeddings and store
- **5. Analyze GitHub repository, check if CI/CD workflow files exist**: `RepoAnalyzer.parse()` calls `_detect_ci()` (ingestion/parsers/repo_analyzer.py:111) to check if repository has CI/CD configured:
    ```python
    def _detect_ci(self, repo_data: dict) -> bool:
        ci_indicators = [
            ".github/workflows" in str(repo_data.get("file_structure", "")),
            ...
        ]
        return any(ci_indicators)
    ```
    - **Note:** currently, _detect_ci() only sets `has_ci = True/False` in metadata in `RepoAnalyzer.parse()`. The workflow YAML content was never read — no skill was extracted.
        ```python
        summary_parts = [
            f"Repository: {repo_data.get('name', 'Unknown')}",
            f"Description: {repo_data.get('description', 'No description')}",
            f"Language: {primary_language}",
            f"Stars: {star_count}",
            f"Forks: {fork_count}",
            f"Open Issues: {open_issues_count}",
            f"Has README: {has_readme}",
            f"Has Tests: {has_tests}",
            f"Has CI/CD: {has_ci}",
            f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Not detected'}",
            f"URL: {repo_data.get('html_url', 'Unknown')}",
        ]
        summary_text = "\n".join(summary_parts)
        metadata = {
            "source_type": "repo",
            "primary_language": primary_language,
            "has_tests": has_tests,
            "has_readme": has_readme,
            "has_ci": has_ci,
            "last_commit_date": last_commit_date,
            "star_count": star_count,
            "fork_count": fork_count,
            "open_issues_count": open_issues_count,
            "tech_stack": tech_stack,
            "repo_name": repo_data.get("name", "Unknown"),
            "repo_url": repo_data.get("html_url", ""),
        }
        return ParseResult(
            text=summary_text,
            metadata=metadata,
            source_type="repo",
        )
        ```
    - We see that `RepoAnalyzer.parse()` also finds out if the repo has_readme, has_tests besides has_ci => we can add a new `IngestionPipeline.ingest_workflow()` function, and let `RepoAnalyzer.parse()` call  `IngestionPipeline.ingest_readme()` and `IngestionPipeline.ingest_workflow()` after RepoAnalyzer.parse() had checked for CI/CD and for readme file. For example:
        ```python
        if repo_result.metadata["has_readme"]:
            readme_content = github_api.fetch_readme(username, repo_name)
            pipeline.ingest_readme(profile_id, repo_name, readme_content)

        if repo_result.metadata["has_ci"]:
            for filename, content in github_api.fetch_workflows(username, repo_name):
                pipeline.ingest_workflow(profile_id, repo_name, filename, content)
        ```        
    - Following the pattern of `IngestionPipeline.ingest_readme()` that makes a call to `readme_parser.parse()`, we should also have a `workflow_parser` class with a `parse()` function, and let `IngestionPipeline.ingest_workflow()` call `workflow_parser.parse()`
        - `workflow_parser.parse()` is supposed to parse the workflow files and return a ParseResult object
            ```python
            class ParseResult:
                """Result of parsing a source document."""
                text: str
                metadata: dict
                source_type: str
            ```
            - `text`: the workflow file text (formatted). Something like:
                ```python
                text_parts = [f"Workflow: {workflow.get('name', 'unnamed')}"]
                for job_name, job in workflow.get("jobs", {}).items():
                    for step in job.get("steps", []):
                        if step.get("uses"):
                            text_parts.append(f"uses: {step['uses']}")
                        if step.get("run"):
                            text_parts.append(f"run: {step['run']}")
                summary_text = "\n".join(text_parts)
                ```
            - `metadata`: something like: 
                ```python
                metadata = {
                    "source_type": "repo_workflow",
                    "workflow_name": workflow_name,
                    "detected_skills": [s.name for s in detected_skills],
                    "ci_tools": [s.name for s in detected if s.category == "Tool"]
                }
                ```
                - notice that we have `SkillExtractor.extract_skills(self, text: str, filename: Optional[str] = None) -> list[SkillDetection]` that extract skills from source code or documentation text => we may use this function to generate `detected_skills` list (need to verify if this use case makes sense)
                ```python
                detected_skills = SkillExtractor.extract_skills(summary_text, filename="workflow.yml")
                ```
                - `extract_skills()` is currently only called in `/tests/unit/test_skill_extractor.py` -> read the test file to see how extract_skills() is used. For example: 
                ```python
                def test_devops_tool_detection(self, extractor):
                    """Test DevOps tool detection."""
                    text = """
                    FROM python:3.9
                    RUN pip install requirements.txt
                    EXPOSE 8000
                    """
                    result = extractor.extract_skills(text)

                    skill_names = [s.name for s in result]
                    # Should detect Docker
                    assert any("docker" in s.lower() for s in skill_names)
                ```

            - `source_type`: "repo_workflow"



-------------------------------------------------------------------------


## What's missing (the three gaps to close)

| Gap | Location | What needs to be added |
|---|---|---|
| No workflow parser | `ingestion/parsers/` | `WorkflowParser` that reads YAML, walks `jobs.<job>.steps`, maps `uses:` and `run:` to skill signals |
| No ingestion entry point | `ingestion/pipeline.py:201` | `ingest_workflow(profile_id, repo_name, content)` method alongside `ingest_readme` |
| No chunking strategy | `ingestion/chunking/strategy_selector.py:14` | `elif source_type == "workflow": return self.semantic_chunker` |

The `_detect_ci()` boolean flag in `RepoAnalyzer` tells you a workflow *exists* but throws away all the content. The fix routes actual YAML content through a new parser before that information is discarded.


-------------------------------------------------------------------------


## ANALYSIS: Replicate Issue #14 (Detailed Steps) 
```
(problem statement: Developers who maintain CI/CD workflows demonstrate DevOps skills that don't appear in import statements or README text. Add a parser that reads .github/workflows/*.yml files and extracts inferred skills (e.g., GitHub Actions, Docker, pytest, deployment).)
```

- **Step 1:** Start the PathReview App Locally, login and start a review request with a resume file + a GitHub username that has repos with CI/CD workflows (Example: Use `actions` (GitHub's own org has workflow files))
- **Step 2:** submit that review request and check the server logs. I should see logs like "Repository metadata chunked successfully" and "Repository embeddings stored", but I do not. Besides I see the log: `[error    ] github_ingestion_failed        error="'raw_data' is an invalid keyword argument for IngestedSource" request_id=1dbbcc01-2fe4-4c29-967c-7770e7a36a22 username=abc` -> no github data or Workflow YAML were fetched
- **Step 3**: read the review result and confirmed no CI/CD skills are extracted (No mention of: Docker, Kubernetes, Terraform, GitHub Actions, CI/CD tools)
- **Step 6**: create a script to replicate issue 14. The script create an example workflow file and use the SkillExtractor.extract_skills(text, filename) to detect skills in that file, then validate the result to check if it correctly detect the skills 
    <details>
    <summary>Click here to expand the script</summary>

    ```bash
    #!/usr/bin/env python3
    """
    Replication script for Issue #14: Add support for parsing GitHub Actions workflow files to detect CI/CD skills

    This script demonstrates that:
    1. SkillExtractor CAN detect CI/CD tools from workflow YAML
    2. But workflow files are never parsed in the production ingestion pipeline
    3. Therefore, CI/CD skills are invisible to developers using GitHub Actions

    Run this script to see what skills SkillExtractor detects from a sample workflow.
    """

    import sys
    from pathlib import Path

    # Add parent directory to path so we can import ingestion modules
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from ingestion.parsers.skill_extractor import SkillExtractor

    # Example GitHub Actions workflow file
    EXAMPLE_WORKFLOW = """
    name: CI/CD Pipeline with GitHub Actions

    on:
    push:
        branches: [main, develop]
    pull_request:
        branches: [main]

    env:
    REGISTRY: ghcr.io
    IMAGE_NAME: myapp
    GITHUB_ACTIONS: true

    jobs:
    build:
        runs-on: ubuntu-latest

        steps:
        - name: Checkout code using GitHub Actions
            uses: actions/checkout@v3

        - name: Set up Python with GitHub Actions
            uses: actions/setup-python@v4
            with:
            python-version: '3.11'

        - name: Install dependencies
            run: |
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            pip install pytest pytest-cov pytest-xdist

        - name: Lint with flake8
            run: flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

        - name: Run pytest unit tests with coverage
            run: |
            pytest tests/ --cov=src/ --cov-report=xml -v
            pytest tests/integration/ --pytest-timeout=60
            pytest tests/e2e/ -m "not slow"

        - name: Upload coverage to Codecov via GitHub Actions
            uses: codecov/codecov-action@v3
            with:
            files: ./coverage.xml

    build-docker:
        needs: build
        runs-on: ubuntu-latest
        permissions:
        contents: read
        packages: write

        steps:
        - name: Checkout code with GitHub Actions
            uses: actions/checkout@v3

        - name: Set up Docker Buildx for multi-platform builds
            uses: docker/setup-buildx-action@v2

        - name: Log in to Docker Container Registry
            uses: docker/login-action@v2
            with:
            registry: ${{ env.REGISTRY }}
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}

        - name: Extract Docker image metadata
            id: meta
            uses: docker/metadata-action@v4
            with:
            images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
            tags: |
                type=ref,event=branch
                type=semver,pattern={{version}}

        - name: Build Docker image and push to registry
            uses: docker/build-push-action@v4
            with:
            context: .
            push: true
            tags: ${{ steps.meta.outputs.tags }}
            labels: ${{ steps.meta.outputs.labels }}
            cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
            cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

        - name: Scan Docker image for vulnerabilities
            run: |
            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \\
                aquasec/trivy image ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

    deploy:
        needs: build-docker
        runs-on: ubuntu-latest
        if: github.ref == 'refs/heads/main'

        steps:
        - name: Checkout code with GitHub Actions
            uses: actions/checkout@v3

        - name: Configure AWS credentials for deployment
            uses: aws-actions/configure-aws-credentials@v2
            with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: us-east-1

        - name: Deploy Docker image to AWS ECS
            run: |
            aws ecs update-service \\
                --cluster production \\
                --service myapp-service \\
                --force-new-deployment

        - name: Deploy infrastructure with Terraform
            run: |
            cd terraform/
            terraform init
            terraform plan -out=tfplan
            terraform apply tfplan

        - name: Configure kubectl for Kubernetes deployment
            uses: azure/setup-kubectl@v3
            with:
            version: 'v1.27.0'

        - name: Deploy Docker image to Kubernetes cluster
            run: |
            kubectl set image deployment/myapp \\
                myapp=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest \\
                -n production
            kubectl rollout status deployment/myapp -n production
            kubectl get deployment myapp -n production

        - name: Run Ansible playbooks for deployment automation
            run: |
            ansible-playbook playbooks/configure-servers.yml
            ansible-playbook playbooks/security-hardening.yml
            ansible-playbook playbooks/post-deployment.yml

        - name: Notify Slack of successful deployment
            uses: slackapi/slack-github-action@v1
            with:
            webhook-url: ${{ secrets.SLACK_WEBHOOK }}
            payload: |
                {
                "text": "Deployment to production completed successfully via GitHub Actions"
                }

        - name: Create GitHub release for deployment
            uses: actions/create-release@v1
            env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            with:
            tag_name: deploy-${{ github.run_number }}
            release_name: Deployment ${{ github.run_number }}
            body: Automated deployment to production
            draft: false
            prerelease: false
    """


    def validate_skill_detection(skills, expected_tools):
        """
        Validate that detected skills include expected CI/CD tools.

        Args:
            skills: List of SkillDetection objects
            expected_tools: Set of tool names that should be detected

        Returns:
            dict: Validation results
        """
        detected_names = {s.name.lower() for s in skills}
        detected_tools = [s for s in skills if s.category == "Tool"]
        detected_tool_names = {s.name.lower() for s in detected_tools}

        results = {
            "total_skills": len(skills),
            "total_tools": len(detected_tools),
            "detected_tool_names": sorted([t.name for t in detected_tools]),
            "expected_tools": sorted(expected_tools),
            "found_tools": sorted(expected_tools & detected_names),
            "missing_tools": sorted(expected_tools - detected_names),
            "validation_passed": expected_tools.issubset(detected_names),
        }

        return results


    def main():
        print("=" * 80)
        print("ISSUE #14 REPLICATION: GitHub Actions Workflow Skill Extraction")
        print("=" * 80)
        print()
        print("Sample workflow includes:")
        print("  • GitHub Actions — checkout, setup-python, docker, kubectl, codecov")
        print("  • Docker — Buildx, image builds, registry push, vulnerability scanning")
        print("  • pytest — unit tests, integration tests, coverage reporting")
        print("  • Deployment — ECS, Kubernetes, Terraform, Ansible, GitHub releases")
        print()

        # Initialize extractor
        extractor = SkillExtractor()

        # Extract skills from the workflow YAML
        print("📝 Analyzing sample GitHub Actions workflow file...")
        print()

        skills = extractor.extract_skills(EXAMPLE_WORKFLOW, filename="ci-cd.yml")

        # Display results
        print(f"✓ Extracted {len(skills)} skills from workflow:\n")

        # Group by category
        by_category = {}
        for skill in skills:
            if skill.category not in by_category:
                by_category[skill.category] = []
            by_category[skill.category].append(skill)

        for category in sorted(by_category.keys()):
            print(f"  {category}:")
            for skill in sorted(by_category[category], key=lambda s: s.confidence, reverse=True):
                print(f"    - {skill.name:<25} (confidence: {skill.confidence:.2f})")
                if skill.evidence:
                    print(f"      Evidence: {', '.join(skill.evidence[:2])}")
            print()

        # Validate detection
        print("-" * 80)
        print("VALIDATION: Expected CI/CD Tools")
        print("-" * 80)

        # These tools are mentioned in the workflow YAML
        expected_ci_cd_tools = {
            "docker",
            "kubernetes",
            "terraform",
            "aws",
            "github",
            "ci/cd",
            "ansible",
        }

        validation = validate_skill_detection(skills, expected_ci_cd_tools)

        print(f"\nTotal skills detected:     {validation['total_skills']}")
        print(f"Total tools detected:      {validation['total_tools']}")
        print()
        print(f"Expected tools:            {', '.join(validation['expected_tools'])}")
        print(f"✓ Found tools:             {', '.join(validation['found_tools'])}")
        if validation["missing_tools"]:
            print(f"✗ Missing tools:           {', '.join(validation['missing_tools'])}")
        print()

        if validation["validation_passed"]:
            print("✓ VALIDATION PASSED: All expected CI/CD tools detected!")
        else:
            print(f"⚠ VALIDATION INCOMPLETE: {len(validation['missing_tools'])} tools not detected")
            print("  This is expected — SkillExtractor uses substring matching")

        # The key issue
        print()
        print("=" * 80)
        print("ISSUE #14: THE GAP")
        print("=" * 80)
        print()
        print("✓ PROVEN: SkillExtractor.extract_skills() CAN detect CI/CD tools")
        print("          from GitHub Actions workflow YAML files.")
        print()
        print("✗ ISSUE:  But workflow files are NEVER passed to SkillExtractor")
        print("          in the production ingestion pipeline.")
        print()
        print("📍 ROOT CAUSE:")
        print("  1. _run_ingestion_pipeline() in review_service.py never calls")
        print("     IngestionPipeline.ingest_resume() or ingest_repo_metadata()")
        print()
        print("  2. RepoAnalyzer._detect_ci() only returns a boolean (has_ci=True/False)")
        print("     without reading the actual workflow YAML content")
        print()
        print("  3. No WorkflowParser exists to parse .github/workflows/*.yml files")
        print()
        print("  4. StrategySelector.select_chunker() has no 'workflow' source_type")
        print()
        print("🔧 SOLUTION: Issue #14 requires:")
        print("  1. Create WorkflowParser class in ingestion/parsers/")
        print("  2. Implement IngestionPipeline.ingest_workflow()")
        print("  3. Add 'workflow' source type to StrategySelector")
        print("  4. Wire _run_ingestion_pipeline() to call IngestionPipeline methods")
        print()
        print("=" * 80)


    if __name__ == "__main__":
        main()

    ```
    </details>

    - **Result:**
        - PROVEN: SkillExtractor.extract_skills() CAN detect CI/CD tools from GitHub Actions workflow YAML files.
        - ISSUE: workflow files are NEVER passed to SkillExtractor in the production ingestion pipeline.

    - **ROOT CAUSE:**
        1. _run_ingestion_pipeline() in review_service.py never calls  IngestionPipeline.ingest_resume() or ingest_repo_metadata()
        2. RepoAnalyzer._detect_ci() only returns a boolean (has_ci=True/False) without reading the actual workflow YAML content
        3. No WorkflowParser exists to parse .github/workflows/*.yml files
        4. StrategySelector.select_chunker() has no 'workflow' source_type

    - **SOLUTION:**
        1. Create WorkflowParser class in ingestion/parsers/
        2. Implement IngestionPipeline.ingest_workflow()
        3. Add 'workflow' source type to StrategySelector
        4. Wire _run_ingestion_pipeline() to call IngestionPipeline methods

-------------------------------------------------------------------------


## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/14 — Add support for parsing GitHub Actions workflow files to detect CI/CD skills

### Understand

**Root cause:** The ingestion pipeline infrastructure exists (SkillExtractor, chunking, embeddings) but is architecturally disconnected from the API layer. When a developer submits a profile with a GitHub username, `_run_ingestion_pipeline()` builds raw dicts without calling `IngestionPipeline.ingest_resume()` or `ingest_repo_metadata()`. Workflow files are never fetched, parsed, or analyzed.

Specifically:
- `RepoAnalyzer._detect_ci()` only checks if `.github/workflows` exists in the file structure and returns a boolean — it never reads the YAML content
- No `WorkflowParser` class exists to parse workflow YAML files
- `IngestionPipeline` has no `ingest_workflow()` method
- `StrategySelector.select_chunker()` has no "workflow" case
- Review feedback is hardcoded; no vector DB queries happen

**Expected behavior:** When a developer's repo contains `.github/workflows/*.yml` files, the system should:
1. Fetch the workflow YAML from GitHub
2. Parse it with `WorkflowParser`, extracting job names, step actions (uses:), and commands (run:)
3. Call `SkillExtractor.extract_skills()` on the assembled text
4. Store detected CI/CD tools (Docker, Kubernetes, Terraform, Ansible, AWS, etc.) in metadata
5. Chunk the workflow content and embed it in ChromaDB
6. Use those skills in review feedback generation

**Current behavior:** Workflow files are never fetched or parsed. CI/CD skills remain invisible. Developers show zero DevOps expertise even if their most skilled work is in GitHub Actions.

### Map

Files I expect to touch:

1. **`ingestion/parsers/skill_extractor.py`** (lines 93–106) — Extend CI/CD tool detection
   - Currently has TOOLS dict with: Docker, Kubernetes, Git, GitHub, AWS, GCP, Azure, CI/CD, Jenkins, Terraform, Ansible
   - Missing CI/CD tools that appear in workflows: Helm, GitLab CI, CircleCI, Codecov, Trivy, PyTest, flake8, pytest-cov
   - Will add these tools to the TOOLS dict with appropriate confidence scores (0.85–0.95 range)
   - May also add Docker Compose, Gradle, Maven, SonarQube if found in test workflows

2. **`ingestion/parsers/workflow_parser.py`** (NEW FILE) — Create `WorkflowParser` class that reads YAML and extracts skills
   - Will follow the pattern of `ResumeParser` and `ReadmeParser` (both inherit from `BaseParser`)
   - Implements `parse(content: str | bytes) -> ParseResult`
   
3. **`ingestion/pipeline.py`** (lines 55–273) — Add `ingest_workflow()` method
   - Will follow the same pattern as `ingest_resume()` (lines 55–125) and `ingest_readme()` (lines 126–200)
   - Takes: `profile_id`, `repo_name`, `filename`, `content` (workflow YAML)
   - Returns: embeddings stored in ChromaDB with `source_type="workflow"` metadata

4. **`ingestion/chunking/strategy_selector.py`** (lines 14–32) — Add "workflow" case to `select_chunker()`
   - Currently only recognizes: "resume", "readme", "repo"
   - Will add: `elif source_type == "workflow": return self.semantic_chunker`

5. **`core/services/review_service.py`** (lines 197–279) — Wire `IngestionPipeline` in `_run_ingestion_pipeline()` (NOTE: might be out of scope)
   - Currently: builds raw dicts, never calls pipeline methods
   - Will change to:
     - Instantiate `IngestionPipeline` with embedding provider and vector DB
     - Call `pipeline.ingest_resume()` if `profile.resume_text` exists
     - Call `pipeline.ingest_repo_metadata()` for each GitHub repo
     - Call `pipeline.ingest_workflow()` for each `.github/workflows/*.yml` file

6. **`tests/unit/test_workflow_parser.py`** (NEW FILE) — Unit tests for `WorkflowParser`
   - Test parsing a realistic GitHub Actions workflow
   - Test skill extraction from workflow YAML
   - Test error handling on malformed YAML


### Plan

**Phase 1: Update skill_extractor.py and Create WorkflowParser**
0. add more ci/cd skill to skill_extractor.py

1. Create `ingestion/parsers/workflow_parser.py`:
   - Import `yaml`, `BaseParser`, `ParseResult`, `SkillExtractor`
   - Implement `WorkflowParser.parse(content: str | bytes) -> ParseResult`:
     - Load YAML with `yaml.safe_load()`
     - Walk `jobs.<job>.steps`, collect `uses:` action names and `run:` commands
     - Assemble into text: `"Workflow: <name>\nuses: <action>\nrun: <command>"`
     - Call `SkillExtractor().extract_skills(text, filename="workflow.yml")`
     - Return `ParseResult(text=assembled_text, metadata={"source_type": "workflow", "detected_skills": [s.name for s in skills], "workflow_name": ...}, source_type="workflow")`

2. Write unit tests in `tests/unit/test_workflow_parser.py`:
   - Test parsing a valid workflow YAML (use the example from `script/replicate_issue_14.py`)
   - Test that `SkillExtractor.extract_skills()` is called and skills are in metadata
   - Test error handling: malformed YAML raises `ValueError`

**Phase 2: Add ingest_workflow() to IngestionPipeline**

3. In `ingestion/pipeline.py`, add `ingest_workflow()` method after `ingest_readme()`:
   - Signature: `async def ingest_workflow(self, profile_id, repo_name, filename, content) -> None`
   - Follow the exact pattern of `ingest_readme()`:
     - Call `WorkflowParser().parse(content)`
     - Pass result to `self.chunker.chunk(parse_result.text, parse_result.metadata)`
     - For each chunk, call `self.embedding_processor.process(chunk, metadata)`
     - Store in ChromaDB with metadata including `source_type="workflow"`

**Phase 3: Update StrategySelector**

4. In `ingestion/chunking/strategy_selector.py`, add workflow case:
   - After line 32 (current repo case), add:
     ```python
     elif source_type == "workflow":
         return self.semantic_chunker
     ```

**Phase 4: Wire the API layer** (NOTE: Out of scope)

5. In `core/services/review_service.py`, update `_run_ingestion_pipeline()`:
   - Import `IngestionPipeline` (already imported on line 10, but will need embedding provider + vector DB)
   - Initialize: `pipeline = IngestionPipeline(db=db, embedding_provider=OpenAIEmbedding(), vector_db=ChromaDB(".chromadb"))`
   - Replace the hardcoded dicts with actual pipeline calls:
     - For resume: `if profile.resume_text: pipeline.ingest_resume(profile.id, profile.resume_text)`
     - For each GitHub repo: `pipeline.ingest_repo_metadata(profile.id, repo_data)`
     - For each workflow in that repo: `pipeline.ingest_workflow(profile.id, repo_name, filename, content)`

6. Update `_run_rag_retrieval_generation()` to actually query ChromaDB:
   - Instead of returning hardcoded dict, use `HybridRetriever` to query for context matching user's skills
   - Call LLM with retrieved context to generate personalized feedback

**Phase 5: Validation**

7. Run unit tests: `make test-unit` — confirm all new tests pass and no new failure appears
8. Run replication script in "ANALYSIS: Replicate Issue #14 (Detailed Steps)" in [PLAN.md](PLAN.md) to confirm no errors
9. Run type checks: `make check` and verify no type errors are related to the new code I added
    - This is equivalent to running:
    ```bash
    make lint       # ruff check .
    make format     # black .
    make typecheck  # mypy api/ core/ ingestion
    ```


### Inputs & outputs

**Functions I'm creating:**

`WorkflowParser.parse(content: str | bytes) -> ParseResult`
- Input: YAML workflow file content (string or bytes)
- Output: `ParseResult` with:
  - `text`: formatted workflow (job names, actions, commands)
  - `metadata`: includes `source_type="workflow"`, `detected_skills: list[str]`, `ci_tools: list[str]`
  - `source_type`: "workflow"

`IngestionPipeline.ingest_workflow(profile_id, repo_name, filename, content) -> None`
- Input: profile ID, repo name, workflow filename, YAML content
- Output: embeddings stored in ChromaDB with workflow metadata

**Test case:**

```python
def test_workflow_parser_extracts_ci_cd_skills():
    """WorkflowParser detects CI/CD tools from GitHub Actions workflow."""
    workflow_yaml = """
    name: CI
    jobs:
      build:
        steps:
          - uses: docker/build-push-action@v2
          - run: terraform apply
    """
    parser = WorkflowParser()
    result = parser.parse(workflow_yaml)
    
    assert result.source_type == "workflow"
    assert "Docker" in result.metadata["detected_skills"]
    assert "Terraform" in result.metadata["detected_skills"]
    assert "uses: docker/build-push-action" in result.text
```

### Risks & unknowns

1. **GitHub API authentication:** Fetching workflow files requires GitHub API access. If no token is configured, this will fail silently (like current code does). I'll need to:
   - Check if `GITHUB_TOKEN` env var exists before calling API
   - Raise `IngestionError` if token is missing, not silently skip
   - Update documentation on required environment variables

2. **Workflow parsing robustness:** YAML can be malformed or non-standard. I need to:
   - Catch `yaml.YAMLError` and raise `ParseError` with clear message
   - Handle missing `jobs:` key gracefully (empty workflow is valid)
   - Test with real-world workflows from major projects to confirm parsing works

3. **Embedding provider initialization:** The current code doesn't show how `OpenAIEmbedding()` is initialized. I need to:
   - Check `ingestion/embeddings/` for the actual class name and constructor
   - Verify the API key is configured
   - Handle rate limiting if processing many workflows

4. **When are workflows fetched?** The current design has no GitHub API client integrated. I need to:
   - Either add a GitHub API client in `core/services/review_service.py`
   - Or have the caller (unknown) pass workflow content via the API
   - The user's current implementation is a placeholder — I need to decide this design before coding

5. **Source type naming:** I used `"workflow"`, but PLAN.md mentions `"repo_workflow"`. I need to:
   - Decide on the canonical name (prefer `"workflow"` — shorter, clearer)
   - Update StrategySelector to match
   - Document in commit message why I chose this name

### Edge cases

1. **Repository with no workflows** — `.github/workflows/` directory exists but is empty
   - Expected: skip gracefully, no error
   - Implementation: `github_api.fetch_workflows(username, repo)` returns empty list; `ingest_workflow()` never called

2. **Repository with workflows but no `jobs:` key** — YAML is present but malformed
   - Expected: raise `ParseError` with message like "Invalid workflow format: no 'jobs' key found"
   - Implementation: `WorkflowParser.parse()` catches `KeyError` and raises `ParseError`

3. **Workflow with mixed action types** — Some steps use `uses:`, others use `run:` with inline scripts
   - Expected: extract both; SkillExtractor detects tools from both action names and script content
   - Implementation: walk all steps, collect both fields

4. **Large workflow files (>100 KB of YAML)** — Some real workflows have thousands of lines
   - Expected: chunk and embed normally; chunker handles large content
   - Implementation: no special handling needed (chunker already handles this for README)

5. **Workflow with secrets/sensitive data in comments** — E.g., `# aws-secret-key = xyz`
   - Expected: no special filtering — we're only indexing tool names, not secrets
   - But: good to document that users shouldn't put actual secrets in workflows (GitHub Actions best practice anyway)
   - Implementation: no changes needed; SkillExtractor only looks for tool keywords

6. **Developer with 50+ repos, some with workflows** — Processing takes a long time
   - Expected: background task completes eventually; doesn't timeout
   - Implementation: depends on how `_run_ingestion_pipeline()` is called (already async/background)
   - May need to document expected runtime

