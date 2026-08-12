import pytest

from ingestion.parsers.web_parser import WebParser


@pytest.fixture
def parser() -> WebParser:
    return WebParser()


def test_parse_extracts_visible_text(parser: WebParser) -> None:
    html = """
    <html>
        <head><title>Rachel's Portfolio</title></head>
        <body>
            <h1>Rachel Lin</h1>
            <p>Software engineer building AI applications.</p>
        </body>
    </html>
    """

    result = parser.parse(html)

    assert "Rachel Lin" in result.text
    assert "Software engineer building AI applications." in result.text
    assert result.metadata["title"] == "Rachel's Portfolio"
    assert result.source_type == "web"


def test_parse_handles_unclosed_script_tag(parser: WebParser) -> None:
    html = """
    <html>
        <body>
            <p>Visible before script</p>
            <script>
                broken script
            <p>Visible after script</p>
        </body>
    </html>
    """

    result = parser.parse(html)

    assert "Visible before script" in result.text
    assert "Visible after script" in result.text


def test_parse_ignores_script_and_style_content(parser: WebParser) -> None:
    html = """
    <html>
        <head>
            <style>.secret { display: none; }</style>
            <script>console.log("hidden script text")</script>
        </head>
        <body>
            <p>Visible portfolio content</p>
        </body>
    </html>
    """

    result = parser.parse(html)

    assert "Visible portfolio content" in result.text
    assert "hidden script text" not in result.text
    assert "display: none" not in result.text


def test_parse_collapses_whitespace(parser: WebParser) -> None:
    html = "<p>Hello      world</p>\n\n<p>Project description</p>"

    result = parser.parse(html)

    assert result.text == "Hello world Project description"


def test_parse_handles_missing_title(parser: WebParser) -> None:
    result = parser.parse("<html><body><p>Portfolio content</p></body></html>")

    assert result.metadata["title"] == ""
    assert result.text == "Portfolio content"


def test_parse_accepts_bytes(parser: WebParser) -> None:
    result = parser.parse(b"<p>Byte content</p>")

    assert result.text == "Byte content"


def test_parse_empty_html(parser: WebParser) -> None:
    result = parser.parse("")

    assert result.text == ""
    assert result.metadata["word_count"] == 0


def test_parse_rejects_unsupported_content_type(parser: WebParser) -> None:
    with pytest.raises(ValueError, match="HTML string or bytes"):
        parser.parse(123)  # type: ignore[arg-type]
