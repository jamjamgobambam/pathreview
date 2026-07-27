"""Integration tests for the full safety middleware chain (issue #75).

The pipeline under test runs a single request through all four guards in order:

    Prompt Defense -> Content Filter -> Bias Detector -> PII Scrubber

Unit tests already cover each guard in isolation (tests/unit/), but nothing
exercises them together. This module will hold pass/fail fixtures for every
layer once the chain is implemented in Week 9.

Reproduction (Week 8): the test below fails on purpose to document that the
integration coverage described in #75 does not exist yet.
"""

import pytest


@pytest.mark.integration
class TestSafetyMiddlewareChain:
    """End-to-end coverage of the composed safety pipeline."""

    def test_full_pipeline_coverage_not_yet_implemented(self) -> None:
        """Reproduction marker for #75 — to be replaced in Week 9.

        Confirms the integration test file lives in the right place and is
        collected by pytest, while making the missing coverage visible as a
        red test rather than a silent gap.
        """
        pytest.fail(
            "Integration coverage for the full safety pipeline is not yet "
            "implemented (issue #75). Prompt Defense -> Content Filter -> "
            "Bias Detector -> PII Scrubber is only tested per-layer in "
            "tests/unit/, never as a chain."
        )
