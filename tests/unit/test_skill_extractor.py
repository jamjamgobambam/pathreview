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

    # this function verifies TypeScript detection without adding a redundant JavaScript result.
    def test_text_with_typescript_files(self, extractor: SkillExtractor) -> None:
        """Cover the issue's TypeScript interface and annotation example."""
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

        skill_names = {skill.name for skill in result}
        # Should detect TypeScript
        # Regression guard: TypeScript syntax should not create a redundant JS skill.
        assert "TypeScript" in skill_names
        assert "JavaScript" not in skill_names

    @pytest.mark.parametrize(
        ("filename", "expected_language"),
        [
            ("src/app.js", "JavaScript"),
            ("src/component.jsx", "JavaScript"),
            ("src/app.ts", "TypeScript"),
            ("src/component.tsx", "TypeScript"),
            # Extension matching is intentionally case-insensitive.
            ("src/COMPONENT.TSX", "TypeScript"),
        ],
    )
    def test_javascript_typescript_filename_extensions(
        self,
        extractor: SkillExtractor,
        filename: str,
        expected_language: str,
    ) -> None:
        """Detect all JavaScript and TypeScript extensions from filename input."""
        result = extractor.extract_skills("Component source", filename=filename)

        assert expected_language in {skill.name for skill in result}

    @pytest.mark.parametrize(
        ("text", "expected_language"),
        [
            ("See src/client.js for the implementation.", "JavaScript"),
            ("See src/client.jsx for the implementation.", "JavaScript"),
            ("See src/client.ts for the implementation.", "TypeScript"),
            ("See src/client.tsx for the implementation.", "TypeScript"),
            ("This service is written in JAVASCRIPT.", "JavaScript"),
            ("This service is written in TypeScript.", "TypeScript"),
        ],
    )
    def test_language_names_and_extensions_in_content(
        self,
        extractor: SkillExtractor,
        text: str,
        expected_language: str,
    ) -> None:
        """Detect boundary-safe file references and explicit language names."""
        result = extractor.extract_skills(text)

        assert expected_language in {skill.name for skill in result}

    def test_tsx_detects_typescript_and_react(self, extractor: SkillExtractor) -> None:
        """A TSX component should retain both its language and framework."""
        text = "import React, { useState } from 'react';"

        result = extractor.extract_skills(text, filename="Counter.tsx")
        skill_names = {skill.name for skill in result}

        assert {"TypeScript", "React"} <= skill_names
        assert "JavaScript" not in skill_names

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
        PostgreSQL database
        import psycopg2
        conn = psycopg2.connect("dbname=mydb")
        """
        result = extractor.extract_skills(text)

        # Fixed the original self-reference so this test evaluates extractor output.
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

    # this function verifies the JavaScript example that originally reproduced issue #148.
    def test_javascript_detection(self, extractor: SkillExtractor) -> None:
        """Cover the issue's JavaScript declaration and CommonJS example."""
        text = """
        const fs = require('fs');
        const data = fs.readFileSync('file.txt');
        console.log(data);
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() or "js" in s.lower() for s in skill_names)

    # Verify arrow-function detection when no filename is available.
    def test_javascript_arrow_function_detection(self, extractor: SkillExtractor) -> None:
        """Require combined JavaScript syntax when no filename is available."""
        text = "const double = (value) => value * 2;"

        result = extractor.extract_skills(text)

        assert "JavaScript" in {skill.name for skill in result}

    @pytest.mark.parametrize(
        "text",
        [
            "import asyncio\nclass Worker:\n    async def run(self):\n        pass",
            "class ReportBuilder implements Builder",
            "Please adjust the settings before continuing.",
        ],
    )
    def test_ambiguous_source_does_not_detect_javascript_or_typescript(
        self,
        extractor: SkillExtractor,
        text: str,
    ) -> None:
        """Shared keywords and extension-like substrings are insufficient evidence."""
        result = extractor.extract_skills(text)
        skill_names = {skill.name for skill in result}

        # These cases protect the evidence thresholds from language false positives.
        assert "JavaScript" not in skill_names
        assert "TypeScript" not in skill_names

    # Verify Compose structure is detected without requiring the word "docker".
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

    @pytest.mark.parametrize(
        "text",
        [
            "services:\n  status: healthy",
            "ports:\n  - 8000",
            "services:\n  web:\n    image: active",
        ],
    )
    def test_generic_yaml_does_not_detect_docker(
        self, extractor: SkillExtractor, text: str
    ) -> None:
        """A single Compose-like key must not label generic YAML as Docker."""
        result = extractor.extract_skills(text)

        assert "Docker" not in {skill.name for skill in result}

    def test_detection_evidence_confidence_and_ordering(self, extractor: SkillExtractor) -> None:
        """Results retain useful evidence, bounded confidence, and sort order."""
        text = """
        TypeScript React application using PostgreSQL and Docker on AWS.
        interface Config { port: number; }
        """

        result = extractor.extract_skills(text)

        # These are public output guarantees called out explicitly in the plan.
        assert result
        assert all(skill.evidence for skill in result)
        assert all(0.0 <= skill.confidence <= 1.0 for skill in result)
        assert [skill.confidence for skill in result] == sorted(
            (skill.confidence for skill in result),
            reverse=True,
        )

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
            name="Python",
            category="Language",
            confidence=0.95,
            evidence=["import statement"],
        )

        assert skill.name == "Python"
        assert skill.category == "Language"
        assert skill.confidence == 0.95
        assert len(skill.evidence) == 1
