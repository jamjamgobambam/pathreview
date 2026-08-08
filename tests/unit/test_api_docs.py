"""Guards docs/API.md against endpoint/example drift (issue #117)."""

import re
from pathlib import Path

import pytest

API_DOC = Path(__file__).resolve().parents[2] / "docs" / "API.md"
ENDPOINT_RE = re.compile(r"^`(GET|POST|PUT|DELETE)\s+([^`]+)`", re.MULTILINE)


@pytest.mark.unit
def test_every_documented_endpoint_has_a_curl_example():
    text = API_DOC.read_text()
    endpoints = ENDPOINT_RE.findall(text)
    assert endpoints, "no endpoints found in docs/API.md — regex or file changed"

    for method, path in endpoints:
        anchor = f"`{method} {path}`"
        idx = text.index(anchor)
        # Next endpoint header or EOF marks this endpoint's block.
        next_match = ENDPOINT_RE.search(text, idx + len(anchor))
        block = text[idx : next_match.start() if next_match else len(text)]
        assert "```bash" in block and "curl" in block, (
            f"{method} {path} is documented but has no curl example"
        )
