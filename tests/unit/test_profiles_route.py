"""Tests for the profile creation route's resume-upload handling.

Guards the two #159 backend defects:
  * the PDF branch must read from ``pypdf`` (not the uninstalled ``PyPDF2``);
  * ``PdfReader`` must receive a file-like object (``io.BytesIO``), not raw bytes.
Both are verified by asserting the parsed ``resume_text`` reaches the
persistence layer (``create_profile``).
"""

import io
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from api.routes.profiles import create_profile_endpoint


def _upload(content: bytes, filename: str, content_type: str) -> Mock:
    """Build a minimal stand-in for FastAPI's ``UploadFile``.

    The route only uses ``filename``, ``content_type`` and an awaitable
    ``read()``, so a light mock keeps the test independent of Starlette.
    """
    upload = Mock()
    upload.filename = filename
    upload.content_type = content_type
    upload.read = AsyncMock(return_value=content)
    return upload


@pytest.mark.unit
class TestCreateProfileResumeUpload:
    """Resume text must be parsed and passed through to create_profile."""

    @pytest.fixture
    def current_user(self) -> Mock:
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_markdown_resume_is_parsed_and_persisted(self, current_user, db):
        content = b"# Jane Doe\nSoftware Engineer\nSkills: Python, FastAPI"
        upload = _upload(content, "resume.md", "text/markdown")

        with (
            patch("api.routes.profiles.create_profile", new_callable=AsyncMock) as mock_create,
            patch("api.routes.profiles.ProfileResponse"),
        ):
            mock_create.return_value = Mock()
            await create_profile_endpoint(
                github_username="janedoe",
                portfolio_url=None,
                resume_file=upload,
                current_user=current_user,
                db=db,
            )

        assert mock_create.await_count == 1
        kwargs = mock_create.await_args.kwargs
        assert kwargs["resume_filename"] == "resume.md"
        assert kwargs["resume_text"] == content.decode("utf-8")

    @pytest.mark.asyncio
    async def test_pdf_resume_reader_gets_bytesio_and_text_is_persisted(self, current_user, db):
        content = b"%PDF-1.4 pretend-these-are-pdf-bytes"
        upload = _upload(content, "resume.pdf", "application/pdf")

        # Fake reader with two pages; the second returns None to exercise the
        # `extract_text() or ""` guard added alongside the BytesIO fix.
        page_one = Mock()
        page_one.extract_text.return_value = "Jane Doe"
        page_two = Mock()
        page_two.extract_text.return_value = None
        fake_reader = Mock()
        fake_reader.pages = [page_one, page_two]
        reader_cls = Mock(return_value=fake_reader)

        with (
            patch("pypdf.PdfReader", reader_cls),
            patch("api.routes.profiles.create_profile", new_callable=AsyncMock) as mock_create,
            patch("api.routes.profiles.ProfileResponse"),
        ):
            mock_create.return_value = Mock()
            await create_profile_endpoint(
                github_username="janedoe",
                portfolio_url=None,
                resume_file=upload,
                current_user=current_user,
                db=db,
            )

        # BytesIO fix: PdfReader must be handed a file-like object wrapping the
        # exact upload bytes, never the raw bytes.
        assert reader_cls.call_count == 1
        (passed_stream,), _ = reader_cls.call_args
        assert isinstance(passed_stream, io.BytesIO)
        assert passed_stream.getvalue() == content

        kwargs = mock_create.await_args.kwargs
        assert kwargs["resume_filename"] == "resume.pdf"
        # "Jane Doe" + "\n".join with the None page coerced to "".
        assert kwargs["resume_text"] == "Jane Doe\n"
