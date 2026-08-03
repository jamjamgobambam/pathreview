"""Tests for benchmark_runner.py"""

import json
from unittest.mock import patch

import pytest

from rag.evaluator.benchmark_runner import (
    DEFAULT_FIXTURES_DIR,
    MIN_CHUNKS_PER_PORTFOLIO,
    SCHEMA_VERSION,
    BenchmarkFixtureError,
    BenchmarkRunner,
    load_benchmark_portfolios,
    parse_portfolio,
    run_benchmarks,
    write_report,
)
from rag.generator.output_parser import FeedbackSection
from rag.retriever.hybrid import HybridRetriever


def _portfolio_payload(**overrides):
    """Build a minimal valid benchmark fixture payload.

    Args:
        **overrides: Fields to replace in the default payload

    Returns:
        Fixture dict
    """
    payload = {
        "portfolio_id": "unit01",
        "description": "Fixture used by the runner unit tests",
        "profile": {"github_username": "testuser", "projects": []},
        "documents": [
            {
                "source_id": "readme_unit01",
                "source_type": "readme",
                "text": (
                    "# Ledger Service\nA small ledger.\n\n"
                    "## Overview\nA python service exposing rest apis built with fastapi "
                    "for recording ledger entries.\n\n"
                    "## Storage\nEntries persist in postgresql and schema changes ship as "
                    "alembic migrations reviewed by the team.\n\n"
                    "## Testing\nBehaviour is covered by pytest cases that run in "
                    "continuous integration on every change.\n\n"
                    "## Deployment\nThe service ships as a docker image promoted through "
                    "a staging environment first."
                ),
            }
        ],
        "queries": ["python fastapi rest apis", "postgresql alembic migrations"],
    }
    payload.update(overrides)
    return payload


def _write_fixture(directory, name, payload):
    """Write a fixture payload to a directory.

    Args:
        directory: Destination directory
        name: File name
        payload: Object to serialise, or a raw string to write verbatim

    Returns:
        Path to the written file
    """
    path = directory / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture
def fixtures_dir(tmp_path):
    """Create a directory holding one valid benchmark fixture."""
    directory = tmp_path / "sample_profiles"
    directory.mkdir()
    _write_fixture(directory, "unit01.json", _portfolio_payload())
    return directory


@pytest.mark.unit
class TestParsePortfolio:
    """Test suite for benchmark fixture validation."""

    def test_valid_payload_parses(self):
        """Test a well formed fixture produces a populated portfolio."""
        portfolio = parse_portfolio(_portfolio_payload(), "unit01.json")

        assert portfolio.portfolio_id == "unit01"
        assert len(portfolio.documents) == 1
        assert portfolio.queries == ["python fastapi rest apis", "postgresql alembic migrations"]

    def test_non_object_payload_rejected(self):
        """Test a JSON array at the top level is rejected."""
        with pytest.raises(BenchmarkFixtureError, match="must be a JSON object"):
            parse_portfolio([], "unit01.json")

    def test_missing_portfolio_id_rejected(self):
        """Test a fixture without portfolio_id is rejected."""
        payload = _portfolio_payload()
        del payload["portfolio_id"]

        with pytest.raises(BenchmarkFixtureError, match="portfolio_id"):
            parse_portfolio(payload, "unit01.json")

    def test_blank_portfolio_id_rejected(self):
        """Test a whitespace-only portfolio_id is rejected."""
        with pytest.raises(BenchmarkFixtureError, match="portfolio_id"):
            parse_portfolio(_portfolio_payload(portfolio_id="   "), "unit01.json")

    def test_missing_documents_rejected(self):
        """Test a fixture without documents is rejected."""
        with pytest.raises(BenchmarkFixtureError, match="documents"):
            parse_portfolio(_portfolio_payload(documents=[]), "unit01.json")

    def test_document_missing_text_rejected(self):
        """Test a document without text is rejected."""
        payload = _portfolio_payload(documents=[{"source_id": "a", "source_type": "readme"}])

        with pytest.raises(BenchmarkFixtureError, match=r"documents\[0\].text"):
            parse_portfolio(payload, "unit01.json")

    def test_document_with_whitespace_text_rejected(self):
        """Test a whitespace-only document is rejected rather than scored as empty."""
        payload = _portfolio_payload(
            documents=[{"source_id": "a", "source_type": "readme", "text": "   \n  "}]
        )

        with pytest.raises(BenchmarkFixtureError, match=r"documents\[0\].text"):
            parse_portfolio(payload, "unit01.json")

    def test_duplicate_source_id_rejected(self):
        """Test two documents sharing a source_id are rejected before they collide."""
        document = {"source_id": "dup", "source_type": "readme", "text": "# A\nsome text"}
        payload = _portfolio_payload(documents=[document, dict(document)])

        with pytest.raises(BenchmarkFixtureError, match="duplicate source_id"):
            parse_portfolio(payload, "unit01.json")

    def test_missing_queries_rejected(self):
        """Test a fixture without queries is rejected."""
        with pytest.raises(BenchmarkFixtureError, match="queries"):
            parse_portfolio(_portfolio_payload(queries=[]), "unit01.json")

    def test_empty_query_rejected(self):
        """Test an empty query string is rejected: RelevanceScorer would score it 0.0."""
        with pytest.raises(BenchmarkFixtureError, match=r"queries\[1\]"):
            parse_portfolio(_portfolio_payload(queries=["valid query", ""]), "unit01.json")

    def test_non_object_profile_rejected(self):
        """Test a non-object profile is rejected."""
        with pytest.raises(BenchmarkFixtureError, match="profile"):
            parse_portfolio(_portfolio_payload(profile="janedoe"), "unit01.json")

    def test_error_message_names_the_fixture(self):
        """Test validation errors identify which fixture failed."""
        with pytest.raises(BenchmarkFixtureError, match="bench99.json"):
            parse_portfolio(_portfolio_payload(queries=[]), "bench99.json")


@pytest.mark.unit
class TestLoadBenchmarkPortfolios:
    """Test suite for loading benchmark fixtures from disk."""

    def test_loads_fixtures_from_directory(self, fixtures_dir):
        """Test every fixture in the directory is loaded."""
        portfolios = load_benchmark_portfolios(fixtures_dir)

        assert len(portfolios) == 1
        assert portfolios[0].portfolio_id == "unit01"

    def test_fixtures_load_in_sorted_filename_order(self, fixtures_dir):
        """Test ordering is stable regardless of filesystem iteration order."""
        _write_fixture(fixtures_dir, "aaa.json", _portfolio_payload(portfolio_id="aaa"))
        _write_fixture(fixtures_dir, "zzz.json", _portfolio_payload(portfolio_id="zzz"))

        ids = [p.portfolio_id for p in load_benchmark_portfolios(fixtures_dir)]

        assert ids == ["aaa", "unit01", "zzz"]

    def test_missing_directory_raises(self, tmp_path):
        """Test a missing fixtures directory fails loudly instead of scoring zeros."""
        with pytest.raises(BenchmarkFixtureError, match="not found"):
            load_benchmark_portfolios(tmp_path / "does_not_exist")

    def test_empty_directory_raises(self, tmp_path):
        """Test an empty fixtures directory fails loudly."""
        empty = tmp_path / "empty"
        empty.mkdir()

        with pytest.raises(BenchmarkFixtureError, match="No benchmark fixtures"):
            load_benchmark_portfolios(empty)

    def test_malformed_json_raises_naming_the_file(self, fixtures_dir):
        """Test invalid JSON is reported against the file that contains it."""
        _write_fixture(fixtures_dir, "broken.json", "{not json")

        with pytest.raises(BenchmarkFixtureError, match="broken.json: invalid JSON"):
            load_benchmark_portfolios(fixtures_dir)

    def test_duplicate_portfolio_id_raises(self, fixtures_dir):
        """Test two fixtures sharing a portfolio_id are rejected."""
        _write_fixture(fixtures_dir, "unit01_copy.json", _portfolio_payload())

        with pytest.raises(BenchmarkFixtureError, match="duplicate portfolio_id"):
            load_benchmark_portfolios(fixtures_dir)

    def test_repository_fixtures_are_valid(self):
        """Test the committed benchmark set loads and meets the corpus size floor."""
        portfolios = load_benchmark_portfolios(DEFAULT_FIXTURES_DIR)

        assert len(portfolios) >= 3
        for portfolio in portfolios:
            assert portfolio.queries
            assert portfolio.documents


@pytest.mark.unit
class TestBenchmarkRunner:
    """Test suite for the offline benchmark runner."""

    @pytest.fixture
    def runner(self):
        """Create a runner pinned to the offline mock provider."""
        return BenchmarkRunner(provider_name="mock")

    @pytest.fixture
    def portfolios(self, fixtures_dir):
        """Load the unit test benchmark portfolio."""
        return load_benchmark_portfolios(fixtures_dir)

    def test_run_produces_a_report(self, runner, portfolios):
        """Test a run scores every portfolio and query."""
        report = runner.run(portfolios)

        assert report.llm_provider == "mock"
        assert len(report.portfolios) == 1
        assert report.query_count == 2

    def test_report_schema_matches_contract(self, runner, portfolios):
        """Test the serialised report has the documented shape."""
        payload = runner.run(portfolios).to_dict()

        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["generated_by"] == "scripts/run_evals.py"
        assert set(payload["aggregate"]) == {
            "relevance_score",
            "faithfulness_score",
            "overall_score",
        }
        portfolio = payload["portfolios"][0]
        assert set(portfolio) == {
            "portfolio_id",
            "description",
            "chunk_count",
            "query_count",
            "queries",
            "relevance_score",
            "faithfulness_score",
            "overall_score",
        }
        assert set(portfolio["queries"][0]) == {
            "query",
            "retrieved_count",
            "generated_sections",
            "retrieval_empty",
            "relevance_score",
            "faithfulness_score",
            "overall_score",
        }

    def test_scores_are_within_range(self, runner, portfolios):
        """Test every reported score is a float between 0 and 1."""
        payload = runner.run(portfolios).to_dict()

        scores = list(payload["aggregate"].values())
        for portfolio in payload["portfolios"]:
            scores.extend([portfolio[key] for key in payload["aggregate"]])
            for query in portfolio["queries"]:
                scores.extend([query[key] for key in payload["aggregate"]])

        assert all(isinstance(score, float) for score in scores)
        assert all(0.0 <= score <= 1.0 for score in scores)

    def test_repeated_runs_produce_identical_json(self, runner, portfolios):
        """Test the runner's core promise: the same inputs give byte-identical output."""
        first = json.dumps(runner.run(portfolios).to_dict(), indent=2, sort_keys=True)
        second = json.dumps(
            BenchmarkRunner(provider_name="mock").run(portfolios).to_dict(),
            indent=2,
            sort_keys=True,
        )

        assert first == second

    def test_retrieval_reaches_the_keyword_index(self, runner, portfolios):
        """Test BM25 contributes to blended scores; without an id join it silently would not."""
        report = runner.run(portfolios)

        assert report.portfolios[0].queries[0].retrieved_count > 0
        assert report.portfolios[0].relevance_score > 0.0

    def test_chunk_count_is_reported(self, runner, portfolios):
        """Test the report records how much corpus each portfolio contributed."""
        report = runner.run(portfolios)

        assert report.portfolios[0].chunk_count >= MIN_CHUNKS_PER_PORTFOLIO

    def test_portfolio_below_chunk_floor_is_rejected(self, runner, fixtures_dir):
        """Test a corpus too small for stable BM25 scoring fails loudly."""
        _write_fixture(
            fixtures_dir,
            "tiny.json",
            _portfolio_payload(
                portfolio_id="tiny",
                documents=[
                    {"source_id": "tiny_doc", "source_type": "resume", "text": "One short line."}
                ],
            ),
        )
        portfolios = load_benchmark_portfolios(fixtures_dir)

        with pytest.raises(BenchmarkFixtureError, match="at least"):
            runner.run(portfolios)

    def test_portfolio_score_is_the_mean_of_its_query_scores(self, runner, portfolios):
        """Test per-portfolio aggregation averages that portfolio's own queries."""
        portfolio = runner.run(portfolios).portfolios[0]

        expected = sum(q.relevance_score for q in portfolio.queries) / len(portfolio.queries)

        assert portfolio.relevance_score == pytest.approx(expected, abs=1e-4)

    def test_aggregate_is_the_mean_of_portfolio_scores(self, runner, fixtures_dir):
        """Test the top-level aggregate averages across portfolios, not across queries."""
        _write_fixture(fixtures_dir, "second.json", _portfolio_payload(portfolio_id="second"))
        report = runner.run(load_benchmark_portfolios(fixtures_dir))

        expected = sum(p.overall_score for p in report.portfolios) / len(report.portfolios)

        assert len(report.portfolios) == 2
        assert report.overall_score == pytest.approx(expected, abs=1e-4)

    def test_overall_score_is_the_mean_of_its_two_components(self, runner, portfolios):
        """Test overall_score stays consistent with EvalSuite's (relevance + faithfulness) / 2."""
        query = runner.run(portfolios).portfolios[0].queries[0]

        expected = (query.relevance_score + query.faithfulness_score) / 2

        assert query.overall_score == pytest.approx(expected, abs=1e-4)

    def test_portfolios_are_isolated_from_each_other(self, runner, fixtures_dir):
        """Test one portfolio's documents never surface in another's retrieval."""
        _write_fixture(
            fixtures_dir,
            "other.json",
            _portfolio_payload(
                portfolio_id="other",
                documents=[
                    {
                        "source_id": "readme_other",
                        "source_type": "readme",
                        "text": (
                            "# Telemetry\nUnrelated.\n\n"
                            "## Collectors\nGathers zirconium metrics from edge nodes.\n\n"
                            "## Storage\nRolls observations into hourly buckets.\n\n"
                            "## Alerting\nPages on sustained anomaly windows.\n\n"
                            "## Retention\nDrops raw samples after thirty days."
                        ),
                    }
                ],
                queries=["zirconium metrics edge nodes"],
            ),
        )
        report = runner.run(load_benchmark_portfolios(fixtures_dir))

        by_id = {p.portfolio_id: p for p in report.portfolios}

        # 'other' has 5 chunks of its own; 'unit01' has 5. Neither may see the other's.
        assert by_id["other"].chunk_count == 5
        assert by_id["unit01"].chunk_count == 5
        for query in by_id["unit01"].queries:
            assert query.retrieved_count <= by_id["unit01"].chunk_count

    def test_keyword_documents_carry_vector_store_ids(self, runner, portfolios):
        """Test BM25 documents are keyed by the same id VectorStore.add_chunks derives."""
        chunks = runner.chunker.chunk(
            portfolios[0].documents[0].text,
            {
                "source_id": portfolios[0].documents[0].source_id,
                "source_type": portfolios[0].documents[0].source_type,
            },
        )

        documents = BenchmarkRunner._keyword_documents(portfolios[0], chunks)

        assert [d["id"] for d in documents] == [
            f"readme_unit01_chunk_{i}" for i in range(len(chunks))
        ]
        assert all(d["text"] and "metadata" in d for d in documents)

    def test_empty_generated_feedback_scores_zero_without_crashing(
        self, runner, portfolios, monkeypatch
    ):
        """Test a generator returning nothing degrades to 0.0 faithfulness, not an exception."""
        monkeypatch.setattr(runner.generator, "generate_full_review", lambda *_: [])

        report = runner.run(portfolios)
        query = report.portfolios[0].queries[0]

        assert query.generated_sections == 0
        assert query.faithfulness_score == 0.0
        assert query.retrieved_count > 0

    def test_blank_generated_feedback_scores_zero(self, runner, portfolios, monkeypatch):
        """Test sections with empty content are treated as no feedback at all."""
        monkeypatch.setattr(
            runner.generator,
            "generate_full_review",
            lambda *_: [FeedbackSection("skills_feedback", "", 0.0, [])],
        )

        query = runner.run(portfolios).portfolios[0].queries[0]

        assert query.faithfulness_score == 0.0

    def test_duplicate_chunk_text_is_rejected(self, runner, fixtures_dir):
        """Test identical chunks are rejected: they tie exactly and break reproducibility."""
        section = "## Overview\nA python service exposing rest apis built with fastapi.\n\n"
        _write_fixture(
            fixtures_dir,
            "tied.json",
            _portfolio_payload(
                portfolio_id="tied",
                documents=[
                    {
                        "source_id": "readme_tied",
                        "source_type": "readme",
                        "text": (
                            "# Tied\nIntro.\n\n"
                            + section
                            + section.replace("## Overview", "## Duplicate")
                            + "## Testing\nCovered by pytest cases.\n\n"
                            "## Deployment\nShips as a docker image."
                        ),
                    }
                ],
            ),
        )
        portfolios = load_benchmark_portfolios(fixtures_dir)

        with pytest.raises(BenchmarkFixtureError, match="identical text"):
            runner.run(portfolios)

    def test_retrieved_chunks_are_sorted_before_scoring(self, runner, portfolios, monkeypatch):
        """Test the runner re-sorts retrieval output, whose order HybridRetriever cannot promise."""
        seen = []

        def capture(profile_data, retrieved_chunks):
            seen.append([chunk["id"] for chunk in retrieved_chunks])
            return []

        monkeypatch.setattr(runner.generator, "generate_full_review", capture)
        monkeypatch.setattr(
            HybridRetriever,
            "retrieve",
            lambda *args, **kwargs: [
                {"id": "b_chunk_0", "text": "beta", "metadata": {}, "score": 0.5},
                {"id": "a_chunk_0", "text": "alpha", "metadata": {}, "score": 0.5},
                {"id": "c_chunk_0", "text": "gamma", "metadata": {}, "score": 0.9},
            ],
        )

        runner.run(portfolios)

        assert seen[0] == ["c_chunk_0", "a_chunk_0", "b_chunk_0"]

    def test_empty_portfolio_list_rejected(self, runner):
        """Test running with no portfolios raises instead of reporting zeros."""
        with pytest.raises(BenchmarkFixtureError, match="No benchmark portfolios"):
            runner.run([])

    def test_empty_retrieval_is_flagged_not_silently_zero(self, runner, portfolios):
        """Test a query that retrieves nothing is distinguishable from a bad score."""
        starved = BenchmarkRunner(provider_name="mock", min_score=1.1)

        report = starved.run(portfolios)
        query = report.portfolios[0].queries[0]

        assert query.retrieved_count == 0
        assert query.retrieval_empty is True
        assert query.relevance_score == 0.0
        assert query.faithfulness_score == 0.0

    def test_empty_retrieval_still_generates_sections(self, runner, portfolios):
        """Test generation degrades gracefully rather than crashing on empty context."""
        starved = BenchmarkRunner(provider_name="mock", min_score=1.1)

        report = starved.run(portfolios)

        assert report.portfolios[0].queries[0].generated_sections > 0

    def test_run_constructs_no_live_model_client(self, runner, portfolios):
        """Test a mock-mode run never builds an OpenAI client."""
        with patch("openai.OpenAI") as mock_client:
            BenchmarkRunner(provider_name="mock").run(portfolios)

        mock_client.assert_not_called()

    def test_run_leaves_no_vector_store_residue(self, runner, portfolios, tmp_path, monkeypatch):
        """Test the temporary Chroma directory is removed when the run finishes."""
        monkeypatch.chdir(tmp_path)
        before = set(tmp_path.iterdir())

        runner.run(portfolios)

        assert not (tmp_path / ".chromadb").exists()
        assert set(tmp_path.iterdir()) == before

    def test_unknown_provider_rejected_at_construction(self):
        """Test an unsupported LLM_PROVIDER fails before any benchmark work starts."""
        with pytest.raises(ValueError):
            BenchmarkRunner(provider_name="not-a-provider")


@pytest.mark.unit
class TestRunBenchmarksAndWriteReport:
    """Test suite for the module level entry points."""

    def test_run_benchmarks_loads_and_runs(self, fixtures_dir):
        """Test run_benchmarks wires loading and running together."""
        report = run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock")

        assert len(report.portfolios) == 1
        assert report.query_count == 2

    def test_run_benchmarks_propagates_fixture_errors(self, tmp_path):
        """Test a missing fixtures directory surfaces as BenchmarkFixtureError."""
        with pytest.raises(BenchmarkFixtureError):
            run_benchmarks(fixtures_dir=tmp_path / "missing", provider_name="mock")

    def test_write_report_creates_file(self, fixtures_dir, tmp_path):
        """Test the report file is created and is valid JSON."""
        report = run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock")
        output = tmp_path / "eval_results.json"

        write_report(report, output)

        assert output.exists()
        assert json.loads(output.read_text())["schema_version"] == SCHEMA_VERSION

    def test_written_report_is_byte_identical_across_runs(self, fixtures_dir, tmp_path):
        """Test two full runs write the same bytes."""
        first = tmp_path / "first.json"
        second = tmp_path / "second.json"

        write_report(run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock"), first)
        write_report(run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock"), second)

        assert first.read_bytes() == second.read_bytes()

    def test_written_report_keys_are_sorted(self, fixtures_dir, tmp_path):
        """Test the report is written with sorted keys so diffs stay readable."""
        output = tmp_path / "eval_results.json"
        write_report(run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock"), output)

        keys = list(json.loads(output.read_text()).keys())

        assert keys == sorted(keys)

    def test_write_report_creates_missing_parent_directories(self, fixtures_dir, tmp_path):
        """Test a report path under a directory that does not exist yet still gets written."""
        report = run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock")
        output = tmp_path / "nested" / "deeper" / "eval_results.json"

        write_report(report, output)

        assert output.exists()

    def test_write_report_raises_when_destination_is_unwritable(self, fixtures_dir, tmp_path):
        """Test a write failure surfaces as OSError rather than a silently missing report."""
        report = run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock")
        blocked = tmp_path / "eval_results.json"
        blocked.mkdir()

        with pytest.raises(OSError):
            write_report(report, blocked)

    def test_report_carries_no_volatile_fields(self, fixtures_dir, tmp_path):
        """Test no timestamp or path is embedded that would break reproducibility."""
        output = tmp_path / "eval_results.json"
        write_report(run_benchmarks(fixtures_dir=fixtures_dir, provider_name="mock"), output)

        payload = json.loads(output.read_text())

        assert "timestamp" not in payload
        assert "generated_at" not in payload
        assert "duration" not in payload
