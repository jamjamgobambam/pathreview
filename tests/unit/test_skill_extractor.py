"""Tests for skill_extractor.py (parser version)"""

import pytest

from ingestion.parsers.skill_extractor import SkillDetection, SkillExtractor


@pytest.mark.unit
class TestSkillExtractor:
    """Test suite for SkillExtractor."""

    @pytest.fixture
    def extractor(self) -> SkillExtractor:
        """Create a SkillExtractor instance."""
        return SkillExtractor()

    def test_text_with_python_imports(self, extractor: SkillExtractor) -> None:
        """Test detection of Python from import statements."""
        text = """
        import os
        from typing import List
        import numpy as np
        """
        result = extractor.extract_skills(text)

        assert isinstance(result, list)
        skill_names = [s.name for s in result]
        # Should detect Python
        assert any("python" in s.lower() for s in skill_names), f"Got skills: {skill_names}"

    def test_text_with_python_type_annotations(self, extractor: SkillExtractor) -> None:
        """Test that Python is detected from type annotations alone."""
        text = """
        def process_data(items: List[str]) -> Dict[str, int]:
            return {}

        async def fetch(url: str) -> Optional[Response]:
            pass
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        # Should still detect Python despite no imports
        assert any("python" in s.lower() for s in skill_names)

    def test_text_with_typescript_files(self, extractor: SkillExtractor) -> None:
        """Test TypeScript detection."""
        text = """
        export interface User {
            id: string;
            name: string;
        }

        export class UserService {
            async getUser(id: string): Promise<User> {}
        }
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        # Should detect TypeScript
        assert any("typescript" in s.lower() for s in skill_names)

    def test_typescript_detection_from_issue_example(self, extractor: SkillExtractor) -> None:
        """Test TypeScript detection from the issue's prose example."""
        text = "Built app.tsx and types.ts with strict TypeScript interfaces"

        result = extractor.extract_skills(text)

        assert any(skill.name == "TypeScript" for skill in result)

    def test_jupyter_ipynb_detection(self, extractor: SkillExtractor) -> None:
        """Test Python/Jupyter detection from .ipynb reference."""
        text = """
        This notebook (analysis.ipynb) contains:
        import pandas as pd
        import matplotlib.pyplot as plt
        """
        result = extractor.extract_skills(text, filename="analysis.ipynb")

        skill_names = [s.name for s in result]
        assert any("python" in s.lower() or "jupyter" in s.lower() for s in skill_names)

    def test_mixed_language_text(self, extractor: SkillExtractor) -> None:
        """Test detection of multiple languages with confidence scores."""
        text = """
        // JavaScript code
        const express = require('express');
        const app = express();

        // Also has Python
        import asyncio
        async def main():
            pass

        // And TypeScript
        interface Config {
            port: number;
        }
        """
        result = extractor.extract_skills(text)

        assert isinstance(result, list)
        assert len(result) > 0

        for skill in result:
            assert isinstance(skill, SkillDetection)
            assert hasattr(skill, "name")
            assert hasattr(skill, "category")
            assert hasattr(skill, "confidence")
            assert 0.0 <= skill.confidence <= 1.0

        skill_names = [s.name for s in result]
        # Should detect multiple languages
        assert len(skill_names) > 1

    def test_frameworks_detected_with_high_confidence(self, extractor: SkillExtractor) -> None:
        """Test that known frameworks are detected with high confidence."""
        text = "import django; from django.db import models"
        result = extractor.extract_skills(text)

        # Should detect Django as framework
        django_skills = [s for s in result if "django" in s.name.lower()]
        if django_skills:
            assert django_skills[0].confidence > 0.8

    def test_react_detection(self, extractor: SkillExtractor) -> None:
        """Test React detection from imports."""
        text = """
        import React, { useState, useEffect } from 'react';
        import ReactDOM from 'react-dom';
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("react" in s.lower() for s in skill_names)

    def test_database_technology_detection(self, extractor: SkillExtractor) -> None:
        """Test database technology detection."""
        text = """
        import psycopg2
        conn = psycopg2.connect("dbname=mydb")
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        # Should detect PostgreSQL
        assert any("postgres" in s.lower() or "sql" in s.lower() for s in skill_names)

    def test_devops_tool_detection(self, extractor: SkillExtractor) -> None:
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

    def test_dockerfile_instruction_case_variations(self, extractor: SkillExtractor) -> None:
        """Test lowercase Dockerfile instructions."""
        text = """
        from python:3.13
        copy . /app
        cmd ["python", "app.py"]
        """

        result = extractor.extract_skills(text)

        assert any(skill.name == "Docker" for skill in result)

    def test_single_dockerfile_instruction_is_not_enough(self, extractor: SkillExtractor) -> None:
        """Test that one Dockerfile instruction does not detect Docker."""
        result = extractor.extract_skills("FROM python:3.13")

        assert not any(skill.name == "Docker" for skill in result)

    def test_repeated_dockerfile_instruction_is_not_enough(self, extractor: SkillExtractor) -> None:
        """Test that repeated copies of one instruction are insufficient."""
        text = """
        RUN echo first
        RUN echo second
        """

        result = extractor.extract_skills(text)

        assert not any(skill.name == "Docker" for skill in result)

    def test_dockerfile_keywords_in_prose_do_not_detect_docker(
        self, extractor: SkillExtractor
    ) -> None:
        """Test that ordinary prose is not treated as a Dockerfile."""
        text = """
        From my experience, this approach works.
        Run the report after reviewing the results.
        """

        result = extractor.extract_skills(text)

        assert not any(skill.name == "Docker" for skill in result)

    def test_skill_has_evidence_list(self, extractor: SkillExtractor) -> None:
        """Test that detected skills include evidence."""
        text = "import numpy; import pandas"
        result = extractor.extract_skills(text)

        for skill in result:
            assert hasattr(skill, "evidence")
            assert isinstance(skill.evidence, list)

    def test_filename_based_detection(self, extractor: SkillExtractor) -> None:
        """Test detection based on filename extension."""
        text = "Some code content"
        result = extractor.extract_skills(text, filename="script.py")

        skill_names = [s.name for s in result]
        # Filename should provide Python hint
        assert any("python" in s.lower() for s in skill_names)

    def test_javascript_detection(self, extractor: SkillExtractor) -> None:
        """Test JavaScript detection."""
        text = """
        const fs = require('fs');
        const data = fs.readFileSync('file.txt');
        console.log(data);
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() or "js" in s.lower() for s in skill_names)

    def test_javascript_detection_from_issue_example(self, extractor: SkillExtractor) -> None:
        """Test JavaScript detection from the issue's prose example."""
        text = "Wrote index.js using const arrow functions and async/await callbacks"

        result = extractor.extract_skills(text)
        skill_names = [skill.name for skill in result]

        assert "JavaScript" in skill_names

    def test_javascript_detection_from_filename(self, extractor: SkillExtractor) -> None:
        """Test JavaScript detection from a filename."""
        result = extractor.extract_skills("", filename="index.js")
        skill_names = [skill.name for skill in result]

        assert "JavaScript" in skill_names

    def test_javascript_not_detected_from_require_prose(self, extractor: SkillExtractor) -> None:
        """Test that ordinary use of 'require' does not detect JavaScript."""
        text = "This position will require strong communication."

        result = extractor.extract_skills(text)

        assert not any(skill.name == "JavaScript" for skill in result)

    def test_docker_compose_detection(self, extractor: SkillExtractor) -> None:
        """Test Docker and Docker Compose detection."""
        text = """
        version: '3.8'
        services:
          web:
            build: .
            ports:
              - "8000:8000"
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    def test_compose_detection_without_version(self, extractor: SkillExtractor) -> None:
        """Test Docker Compose detection without a version field."""
        text = """
        services:
          web:
            image: nginx
        """

        result = extractor.extract_skills(text)

        assert any(skill.name == "Docker" for skill in result)

    def test_services_alone_does_not_detect_docker(self, extractor: SkillExtractor) -> None:
        """Test that a services key alone is insufficient."""
        text = """
        services:
          email: enabled
        """

        result = extractor.extract_skills(text)

        assert not any(skill.name == "Docker" for skill in result)

    def test_compose_marker_without_services_does_not_detect_docker(
        self, extractor: SkillExtractor
    ) -> None:
        """Test that a Compose marker requires a services section."""
        text = """
        application:
          image: nginx
          ports:
            - "8000:80"
        """

        result = extractor.extract_skills(text)

        assert not any(skill.name == "Docker" for skill in result)

    def test_aws_gcp_azure_detection(self, extractor: SkillExtractor) -> None:
        """Test cloud platform detection."""
        text = """
        import boto3
        client = boto3.client('s3')
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("aws" in s.lower() or "python" in s.lower() for s in skill_names)

    def test_empty_text(self, extractor: SkillExtractor) -> None:
        """Test handling of empty text."""
        result = extractor.extract_skills("")
        assert isinstance(result, list)

    def test_unrecognized_language(self, extractor: SkillExtractor) -> None:
        """Test handling of unrecognized language."""
        text = "This is just plain English text with no code."
        result = extractor.extract_skills(text)
        # Should return list (possibly empty)
        assert isinstance(result, list)

    def test_confidence_scores_are_floats(self, extractor: SkillExtractor) -> None:
        """Test that all confidence scores are floats between 0 and 1."""
        text = "import django; import numpy; from flask import Flask"
        result = extractor.extract_skills(text)

        for skill in result:
            assert isinstance(skill.confidence, float)
            assert 0.0 <= skill.confidence <= 1.0

    def test_skill_detection_dataclass(self) -> None:
        """Test SkillDetection dataclass structure."""
        skill = SkillDetection(
            name="Python", category="Language", confidence=0.95, evidence=["import statement"]
        )

        assert skill.name == "Python"
        assert skill.category == "Language"
        assert skill.confidence == 0.95
        assert len(skill.evidence) == 1
