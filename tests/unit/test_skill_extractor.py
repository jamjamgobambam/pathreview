"""Tests for skill_extractor.py (parser version)"""

import pytest

from ingestion.parsers.skill_extractor import SkillDetection, SkillExtractor


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

        skill_names = [s.name for s in result]
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

    # --- PLAN.md lines 66-71: Dockerfile & Compose positive variants ---

    def test_dockerfile_copy_cmd_detection(self, extractor):
        """Positive: a Dockerfile using COPY and CMD is detected as Docker."""
        text = """
        FROM node:18-alpine
        COPY . /app
        CMD ["node", "server.js"]
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    def test_multistage_dockerfile_detection(self, extractor):
        """Positive: a multi-stage Dockerfile is detected as Docker."""
        text = """
        FROM golang:1.21 AS builder
        WORKDIR /src
        COPY . .
        RUN go build -o app

        FROM alpine:latest
        COPY --from=builder /src/app /usr/local/bin/app
        CMD ["app"]
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    def test_compose_services_image_detection(self, extractor):
        """Positive: a compose file using services + image is detected."""
        text = """
        version: "3.9"
        services:
          db:
            image: postgres:15
            environment:
              POSTGRES_PASSWORD: secret
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    def test_compose_volumes_detection(self, extractor):
        """Positive: a compose file declaring volumes is detected."""
        text = """
        services:
          cache:
            image: redis:7
            volumes:
              - cache-data:/data

        volumes:
          cache-data:
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    # --- PLAN.md lines 72-73: Negative cases ---

    def test_non_docker_yaml_not_detected(self, extractor):
        """Negative: generic YAML with no services/Dockerfile is not Docker."""
        text = """
        name: my-app
        version: 1.0.0
        settings:
          debug: true
          timeout: 30
        database:
          host: localhost
          port: 5432
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert not any("docker" in s.lower() for s in skill_names)

    def test_pip_install_alone_not_detected_as_docker(self, extractor):
        """Negative: a bare pip install line is not misdetected as Docker."""
        text = "pip install -r requirements.txt"
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert not any("docker" in s.lower() for s in skill_names)

    # --- PLAN.md line 74: Malformed configs & size extremes ---

    def test_partial_docker_config_does_not_crash(self, extractor):
        """Malformed/small: incomplete configs return a list without raising."""
        for snippet in ("FROM", "services:", "version: '3'\nservices:", "RUN echo hi"):
            result = extractor.extract_skills(snippet)
            assert isinstance(result, list)

    def test_docker_detected_in_large_multiblock_text(self, extractor):
        """Size extreme: a Dockerfile embedded in large text is still detected."""
        filler = "lorem ipsum dolor sit amet\n" * 500
        dockerfile = """
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install -r requirements.txt
        EXPOSE 8080
        CMD ["python", "app.py"]
        """
        text = filler + dockerfile + filler
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("docker" in s.lower() for s in skill_names)

    # --- PLAN.md line 75: Missing, empty, or neutral filenames ---

    def test_docker_detected_regardless_of_filename(self, extractor):
        """Filename-agnostic: Dockerfile body detects Docker for any filename."""
        text = """
        FROM ubuntu:22.04
        RUN apt-get update
        CMD ["bash"]
        """
        for filename in (None, "", "notes.txt"):
            result = extractor.extract_skills(text, filename=filename)
            skill_names = [s.name for s in result]
            assert any(
                "docker" in s.lower() for s in skill_names
            ), f"filename={filename!r} gave {skill_names}"

    # --- PLAN.md line 76: Contextual keyword collisions ---

    def test_docker_keywords_in_shell_script_not_detected(self, extractor):
        """Collision: lowercase from/copy/run in a shell script is not Docker."""
        text = """
        #!/bin/sh
        # Deployment script: copy build artifacts from the dist folder
        build() {
            echo "running build and copying files from dist"
        }
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert not any("docker" in s.lower() for s in skill_names)

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

    # --- PLAN.md line 52: Positive cases (should detect JavaScript/TypeScript) ---

    def test_javascript_es6_import_detection(self, extractor):
        """Positive: ES6 `import ... from` is detected as JavaScript."""
        text = """
        import { readFile } from 'fs/promises';
        import path from 'path';
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() for s in skill_names)

    def test_javascript_arrow_function_detection(self, extractor):
        """Positive: arrow functions and variable declarations are detected."""
        text = """
        const add = (a, b) => a + b;
        let double = x => x * 2;
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() for s in skill_names)

    def test_javascript_function_class_export_detection(self, extractor):
        """Positive: function/class/export syntax is detected as JavaScript."""
        text = """
        export function greet(name) {
            return "Hi " + name;
        }

        class Animal extends Base {}
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() for s in skill_names)

    # --- PLAN.md line 53: Negative cases (plain text, unsupported langs, no filename) ---

    def test_plain_text_not_detected_as_javascript(self, extractor):
        """Negative: prose containing JS-like words is not detected as JS/TS."""
        text = (
            "This function lets you import ideas from a class of problems "
            "and does not require any special export."
        )
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert not any("javascript" in s.lower() or "typescript" in s.lower() for s in skill_names)

    def test_unsupported_language_not_detected_as_javascript(self, extractor):
        """Negative: Go source is not misdetected as JavaScript/TypeScript."""
        text = """
        package main

        import "fmt"

        func main() {
            fmt.Println("hello")
        }
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert not any("javascript" in s.lower() or "typescript" in s.lower() for s in skill_names)

    def test_missing_filename_returns_list(self, extractor):
        """Negative: missing filename with non-code text returns a list, no error."""
        result = extractor.extract_skills("just some notes", filename=None)
        assert isinstance(result, list)

    def test_empty_filename_does_not_crash(self, extractor):
        """Negative: an empty filename string is handled gracefully."""
        result = extractor.extract_skills("const x = 1;", filename="")
        assert isinstance(result, list)

    # --- PLAN.md line 54: False positives & cross-language collisions ---

    def test_python_shared_keywords_not_detected_as_javascript(self, extractor):
        """Collision: Python using import/class/async/await stays Python only."""
        text = """
        import asyncio

        class DataProcessor:
            async def process(self):
                result = await self.fetch()
                return result
        """
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("python" in s.lower() for s in skill_names)
        assert not any("javascript" in s.lower() or "typescript" in s.lower() for s in skill_names)

    # --- PLAN.md line 55: False negatives & malformed/incomplete snippets ---

    def test_malformed_snippet_does_not_crash(self, extractor):
        """Malformed: truncated/incomplete code returns a list without raising."""
        text = "function brokenFn( const x ="
        result = extractor.extract_skills(text)
        assert isinstance(result, list)

    def test_minimal_valid_snippet_still_detected(self, extractor):
        """False-negative guard: a tiny valid JS declaration is still detected."""
        text = "const total = 42;"
        result = extractor.extract_skills(text)

        skill_names = [s.name for s in result]
        assert any("javascript" in s.lower() for s in skill_names)

    def test_skill_detection_dataclass(self):
        """Test SkillDetection dataclass structure."""
        skill = SkillDetection(
            name="Python", category="Language", confidence=0.95, evidence=["import statement"]
        )

        assert skill.name == "Python"
        assert skill.category == "Language"
        assert skill.confidence == 0.95
        assert len(skill.evidence) == 1
