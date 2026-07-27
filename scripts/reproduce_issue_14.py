"""
Reproduction script for Issue #14:
Add support for parsing GitHub Actions workflow files to detect CI/CD skills

This script creates a minimal test repository with a GitHub Actions workflow file,
then runs the current SkillExtractor against it to demonstrate that CI/CD skills
are completely missed.

Usage:
    python reproduce_issue_14.py

Expected output: Zero CI/CD skills detected, confirming the bug.
"""

import os
import shutil

# Add the project root to Python path so we can import ingestion modules
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ingestion.parsers.skill_extractor import SkillExtractor


def create_test_repo_with_workflow() -> str:
    """Create a temporary directory with a .github/workflows/ci.yml file."""
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    workflows_dir = Path(temp_dir) / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    ci_yml = workflows_dir / "ci.yml"
    ci_yml.write_text(
        """
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run pytest
        run: pytest tests/ -v
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: myapp:latest

  deploy:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying application..."
          kubectl apply -f k8s/
"""
    )

    return temp_dir


def main() -> None:
    print("=" * 60)
    print("Issue #14 Reproduction: CI/CD skills from workflow files")
    print("=" * 60)

    # Create test repository
    repo_path = create_test_repo_with_workflow()
    workflow_file = Path(repo_path) / ".github" / "workflows" / "ci.yml"
    print(f"\nCreated test repo at: {repo_path}")
    print(f"Workflow file exists: {workflow_file.exists()}")

    # Read the workflow file content
    workflow_text = workflow_file.read_text()
    print(f"Workflow file size: {len(workflow_text)} chars")
    print(f"Workflow contains 'actions/checkout': {'actions/checkout' in workflow_text}")
    print(f"Workflow contains 'docker': {'docker' in workflow_text.lower()}")
    print(f"Workflow contains 'pytest': {'pytest' in workflow_text.lower()}")
    print(f"Workflow contains 'deployment': {'deploy' in workflow_text.lower()}")

    # Run SkillExtractor on the workflow text
    extractor = SkillExtractor()
    skills = extractor.extract_skills(workflow_text, filename="ci.yml")

    print("\n" + "-" * 60)
    print("SKILL EXTRACTION RESULTS:")
    print("-" * 60)

    if not skills:
        print("NO SKILLS DETECTED — BUG CONFIRMED")
        print("\nExpected: GitHub Actions, Docker, pytest, deployment, Kubernetes")
        print("Actual: None")
    else:
        print(f"Detected {len(skills)} skill(s):")
        for skill in skills:
            print(f"  - {skill.name} ({skill.category}, confidence={skill.confidence:.2f})")

    # Check specifically for CI/CD skills
    ci_cd_skills = ["GitHub Actions", "Docker", "pytest", "deployment", "Kubernetes", "CI/CD"]
    detected_names = {s.name for s in skills}
    missing = [s for s in ci_cd_skills if s not in detected_names]

    print("\n" + "-" * 60)
    print("CI/CD SKILL GAP ANALYSIS:")
    print("-" * 60)
    if missing:
        print(f"Missing CI/CD skills: {', '.join(missing)}")
        print("\nROOT CAUSE: workflow .yml files are not parsed by the ingestion pipeline,")
        print("and even if they were, keywords like 'github actions', 'pytest', 'deployment'")
        print("are absent from SkillExtractor.TOOLS")
    else:
        print("All CI/CD skills detected — issue may already be fixed.")

    # Cleanup
    shutil.rmtree(repo_path)
    print(f"\nCleaned up temp directory: {repo_path}")
    print("\n" + "=" * 60)
    print("Reproduction complete. Commit this script to document the issue.")
    print("=" * 60)


if __name__ == "__main__":
    main()
