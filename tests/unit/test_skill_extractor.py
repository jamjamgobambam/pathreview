"""Tests for skill_extractor.py (parser version)"""

import pytest

from ingestion.parsers.skill_extractor import SkillExtractor, SkillDetection


@pytest.mark.unit
class TestSkillExtractor:
    """Test suite for SkillExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create a SkillExtractor instance."""
        return SkillExtractor()

    def test_text_with_python_imports(self, extractor):
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

    def test_text_with_python_type_annotations(self, extractor):
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

    def test_text_with_typescript_files(self, extractor):
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

    def test_jupyter_ipynb_detection(self, extractor):
        """Test Python/Jupyter detection from .ipynb reference."""
        text = """
        This notebook (analysis.ipynb) contains:
        import pandas as pd
        import matplotlib.pyplot as plt
        """
        result = extractor.extract_skills(text, filename="analysis.ipynb")

        skill_names = [s.name for s in result]
        assert any("python" in s.lower() or "jupyter" in s.lower() for s in skill_names)

    def test_mixed_language_text(self, extractor):
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

    def test_frameworks_detected_with_high_confidence(self, extractor):
        """Test that known frameworks are detected with high confidence."""
        text = "import django; from django.db import models"
        result = extractor.extract_skills(text)

        # Should detect Django as framework
        django_skills = [s for s in result if "django" in s.name.lower()]
        if django_skills:
            assert django_skills[0].confidence > 0.8

    def test_react_detection(self, extractor):
        """Test React detection from imports."""
        text = """
        import React, { useState, useEffect } from 'react';
        import ReactDOM from 'react-dom';
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("react" in s.lower() for s in skill_names)

    def test_database_technology_detection(self, extractor):
        """Test database technology detection."""
        text = """
        import psycopg2
        conn = psycopg2.connect("dbname=mydb")
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in skill_names]
        # Should detect PostgreSQL
        assert any("postgres" in s.lower() or "sql" in s.lower() for s in skill_names)

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

    def test_skill_has_evidence_list(self, extractor):
        """Test that detected skills include evidence."""
        text = "import numpy; import pandas"
        result = extractor.extract_skills(text)

        for skill in result:
            assert hasattr(skill, "evidence")
            assert isinstance(skill.evidence, list)

    def test_filename_based_detection(self, extractor):
        """Test detection based on filename extension."""
        text = "Some code content"
        result = extractor.extract_skills(text, filename="script.py")

        skill_names = [s.name for s in result]
        # Filename should provide Python hint
        assert any("python" in s.lower() for s in skill_names)

    def test_javascript_detection(self, extractor):
        """Test JavaScript detection."""
        text = """
        const fs = require('fs');
        const data = fs.readFileSync('file.txt');
        console.log(data);
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() or "js" in s.lower() for s in skill_names)

    def test_docker_compose_detection(self, extractor):
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

    def test_aws_gcp_azure_detection(self, extractor):
        """Test cloud platform detection."""
        text = """
        import boto3
        client = boto3.client('s3')
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("aws" in s.lower() or "python" in s.lower() for s in skill_names)

    def test_empty_text(self, extractor):
        """Test handling of empty text."""
        result = extractor.extract_skills("")
        assert isinstance(result, list)

    def test_unrecognized_language(self, extractor):
        """Test handling of unrecognized language."""
        text = "This is just plain English text with no code."
        result = extractor.extract_skills(text)
        # Should return list (possibly empty)
        assert isinstance(result, list)

    def test_confidence_scores_are_floats(self, extractor):
        """Test that all confidence scores are floats between 0 and 1."""
        text = "import django; import numpy; from flask import Flask"
        result = extractor.extract_skills(text)

        for skill in result:
            assert isinstance(skill.confidence, float)
            assert 0.0 <= skill.confidence <= 1.0

    def test_skill_detection_dataclass(self):
        """Test SkillDetection dataclass structure."""
        skill = SkillDetection(
            name="Python",
            category="Language",
            confidence=0.95,
            evidence=["import statement"]
        )

        assert skill.name == "Python"
        assert skill.category == "Language"
        assert skill.confidence == 0.95
        assert len(skill.evidence) == 1
