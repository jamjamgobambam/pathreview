"""Tests for scripts/run_evals.py"""

import json
from pathlib import Path

import pytest

import scripts.run_evals as run_evals
from ingestion.embeddings.provider import EmbeddingProvider, get_embedding_provider
from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestRunEvals:
    """Test suite for the offline eval runner."""

    @pytest.fixture
    def sample_fixture(self) -> dict:
        """A minimal valid benchmark fixture."""
        return {
            "profile_id": "test_profile_01",
            "github_username": "test-user",
            "projects": ["some-project"],
            "query": "How is this candidate's portfolio?",
            "chunks": [
                {
                    "source_id": "readme",
                    "section": "overview",
                    "text": "some-project is a Python tool.",
                },
            ],
        }

    def test_load_fixtures_finds_real_fixtures(self) -> None:
        """Test load_fixtures reads the real benchmark fixture files."""
        fixtures = run_evals.load_fixtures()

        assert len(fixtures) >= 1
        for fixture in fixtures:
            assert "profile_id" in fixture
            assert "query" in fixture
            assert "chunks" in fixture

    def test_evaluate_fixture_returns_scores(
        self, tmp_path: Path, sample_fixture: dict
    ) -> None:
        """Test evaluate_fixture runs the full pipeline and returns scores."""
        vector_store = VectorStore(persist_dir=str(tmp_path))
        embedding_provider: EmbeddingProvider = get_embedding_provider("mock")

        result = run_evals.evaluate_fixture(sample_fixture, vector_store, embedding_provider)

        assert result["profile_id"] == "test_profile_01"
        assert "error" not in result
        assert 0.0 <= result["relevance_score"] <= 1.0
        assert 0.0 <= result["faithfulness_score"] <= 1.0
        assert 0.0 <= result["overall_score"] <= 1.0
        assert result["chunks_retrieved"] >= 1
        assert result["sections_generated"] == 5

    def test_evaluate_fixture_handles_empty_chunks_gracefully(self, tmp_path: Path) -> None:
        """Test a fixture with no chunks does not crash the run."""
        vector_store = VectorStore(persist_dir=str(tmp_path))
        embedding_provider: EmbeddingProvider = get_embedding_provider("mock")

        empty_fixture = {
            "profile_id": "empty_profile",
            "github_username": "nobody",
            "projects": [],
            "query": "How is this portfolio?",
            "chunks": [],
        }

        result = run_evals.evaluate_fixture(empty_fixture, vector_store, embedding_provider)

        assert result["profile_id"] == "empty_profile"

    def test_main_writes_valid_json_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_fixture: dict
    ) -> None:
        """Test main() end to end writes a well-formed eval_results.json."""
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        (fixtures_dir / "profile_01.json").write_text(json.dumps(sample_fixture))

        output_path = tmp_path / "eval_results.json"

        monkeypatch.setattr(run_evals, "FIXTURES_DIR", fixtures_dir)
        monkeypatch.setattr(run_evals, "OUTPUT_PATH", output_path)

        run_evals.main()

        assert output_path.exists()
        report = json.loads(output_path.read_text())

        assert report["profiles_evaluated"] == 1
        assert report["profiles_failed"] == 0
        assert 0.0 <= report["average_overall_score"] <= 1.0
        assert len(report["results"]) == 1

    def test_main_exits_when_no_fixtures_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test main() exits cleanly if the fixtures directory is empty."""
        empty_dir = tmp_path / "empty_fixtures"
        empty_dir.mkdir()

        monkeypatch.setattr(run_evals, "FIXTURES_DIR", empty_dir)

        with pytest.raises(SystemExit):
            run_evals.main()
