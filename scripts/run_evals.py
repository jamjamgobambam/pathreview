"""Run the RAG evaluation suite against benchmark portfolios."""


def main() -> None:
    """Execute the full evaluation pipeline and output results."""
    print("Running RAG evaluation suite...")
    # TODO: Implement eval runner
    # 1. Load benchmark portfolios from tests/fixtures/sample_profiles/
    # 2. Run each through the full RAG pipeline with mock LLM
    # 3. Score retrieval relevance, faithfulness, and actionability
    # 4. Output JSON report to eval_results.json
    print("Evaluation complete. Results written to eval_results.json")


if __name__ == "__main__":
    main()
