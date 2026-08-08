"""Tests for public service function docstrings."""

from collections.abc import Callable

import pytest

from core.services.profile_service import (
    create_profile,
    delete_profile,
    get_profile,
    update_profile,
)
from core.services.review_service import (
    create_review,
    get_review,
    list_reviews,
    process_review,
)

PUBLIC_SERVICE_FUNCTIONS = [
    create_profile,
    delete_profile,
    get_profile,
    update_profile,
    create_review,
    get_review,
    list_reviews,
    process_review,
]


@pytest.mark.unit
class TestServiceDocstrings:
    """Test suite for public service function docstrings."""

    @pytest.mark.parametrize("service_function", PUBLIC_SERVICE_FUNCTIONS)
    def test_public_functions_have_docstrings(
        self, service_function: Callable[..., object]
    ) -> None:
        """Test that each public service function has a nonempty docstring."""
        assert service_function.__doc__ is not None
        assert service_function.__doc__.strip()

    @pytest.mark.parametrize("service_function", PUBLIC_SERVICE_FUNCTIONS)
    def test_public_function_docstrings_include_required_sections(
        self,
        service_function: Callable[..., object],
    ) -> None:
        """Test that each public function documents its arguments and return value."""
        docstring = service_function.__doc__

        assert docstring is not None
        assert "Args:" in docstring
        assert "Returns:" in docstring
