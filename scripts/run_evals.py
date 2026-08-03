"""Run the RAG evaluation suite against benchmark portfolios.

Thin CLI over rag.evaluator.benchmark_runner. The pipeline itself lives under
rag/ because scripts/ is excluded from the installed distribution
(pyproject.toml [tool.setuptools.packages.find]) and so would not be reliably
importable by tests or by an installed copy of the package.

Usage:
    LLM_PROVIDER=mock python scripts/run_evals.py
"""

import argparse
import sys
from pathlib import Path

# Running this file directly puts scripts/ on sys.path rather than the repo
# root, so the repo root is added explicitly for the uninstalled case.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.evaluator.benchmark_runner import (  # noqa: E402
    DEFAULT_FIXTURES_DIR,
    DEFAULT_OUTPUT_PATH,
    BenchmarkFixtureError,
    BenchmarkReport,
    run_benchmarks,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Run the offline RAG evaluation suite over the benchmark portfolio set."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help=f"Directory of benchmark portfolio fixtures (default: {DEFAULT_FIXTURES_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Where to write the JSON report (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser


def format_summary(report: BenchmarkReport, output_path: Path) -> str:
    """Render a short human readable summary of a run.

    Args:
        report: The completed report
        output_path: Where the JSON report was written

    Returns:
        Multi-line summary string
    """
    lines = [
        f"Provider:   {report.llm_provider}",
        f"Portfolios: {len(report.portfolios)}",
        f"Queries:    {report.query_count}",
        "",
        f"{'portfolio':<12} {'chunks':>7} {'relevance':>10} {'faithful':>10} {'overall':>9}",
    ]
    for portfolio in report.portfolios:
        lines.append(
            f"{portfolio.portfolio_id:<12} {portfolio.chunk_count:>7} "
            f"{portfolio.relevance_score:>10.4f} {portfolio.faithfulness_score:>10.4f} "
            f"{portfolio.overall_score:>9.4f}"
        )
    lines.extend(
        [
            f"{'AGGREGATE':<12} {'':>7} {report.relevance_score:>10.4f} "
            f"{report.faithfulness_score:>10.4f} {report.overall_score:>9.4f}",
            "",
            f"Results written to {output_path}",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Execute the full evaluation pipeline and output results.

    The report is written as soon as the run completes so CI always has a
    readable artifact to publish. A completed run exits 0 whatever the scores
    are: no score thresholds, golden outputs or baselines exist anywhere in this
    repository, so failing the build against an invented threshold would turn a
    quality signal into an arbitrary merge block. A non-zero exit means the
    evaluation could not run at all — missing or malformed fixtures, an
    unusable LLM_PROVIDER, or an error part-way through the pipeline.

    Args:
        argv: Command line arguments; defaults to sys.argv[1:]

    Returns:
        Process exit code
    """
    args = build_parser().parse_args(argv)

    print("Running RAG evaluation suite...")

    try:
        report = run_benchmarks(fixtures_dir=args.fixtures_dir)
    except BenchmarkFixtureError as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Raised by the provider factories for an unrecognised LLM_PROVIDER, or
        # for a live provider selected without its API key. A traceback would
        # bury a message the operator can act on directly.
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    output_path = write_report(report, args.output)
    print(format_summary(report, output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
