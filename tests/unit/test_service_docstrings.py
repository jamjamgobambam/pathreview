"""Tests for the Google-style docstrings in core/services/.

These tests check the structure of the service layer's documentation rather
than its runtime behavior. CONTRIBUTING.md requires Google-style docstrings on
all public functions, and a docstring that has silently drifted out of sync
with its signature is worse than no docstring at all — it actively misleads.
So each check is written against the real signature via introspection: adding
a parameter without documenting it, or renaming one without updating the
docstring, fails here.
"""

import ast
import inspect
import re
import textwrap
from collections.abc import Callable
from types import ModuleType
from typing import Any

import pytest

from core.services import profile_service, review_service

SERVICE_MODULES = (profile_service, review_service)

# A discovered function: the module defining it, its name, and the function.
ServiceFunction = tuple[ModuleType, str, Callable[..., Any]]

# Section headers recognized by Google-style docstrings, in canonical order.
GOOGLE_SECTIONS = (
    "Args",
    "Returns",
    "Yields",
    "Raises",
    "Note",
    "Notes",
    "Example",
    "Examples",
)

_SECTION_RE = re.compile(rf"^({'|'.join(GOOGLE_SECTIONS)}):\s*$")

# A parameter entry sits at exactly four spaces of indentation once the
# docstring is dedented; continuation lines are indented further and so are
# skipped, which keeps colons inside a description from being misread.
_PARAM_RE = re.compile(r"^ {4}(\w+)\s*(?:\([^)]*\))?:\s*(.*)$")

# The public API of the service layer. Asserted below so that a broken
# discovery helper fails loudly instead of silently collecting nothing and
# leaving every parametrized test vacuously green.
EXPECTED_PUBLIC_FUNCTIONS = {
    "create_profile",
    "get_profile",
    "update_profile",
    "delete_profile",
    "create_review",
    "get_review",
    "list_reviews",
    "process_review",
}


def _module_functions(module: ModuleType) -> list[ServiceFunction]:
    """Return (module, name, function) for functions defined in the module."""
    return [
        (module, name, obj)
        for name, obj in vars(module).items()
        if inspect.isfunction(obj) and obj.__module__ == module.__name__
    ]


ALL_FUNCTIONS: list[ServiceFunction] = [
    entry for module in SERVICE_MODULES for entry in _module_functions(module)
]

FUNCTION_CASES = [
    pytest.param(entry, id=f"{entry[0].__name__.rsplit('.', 1)[-1]}.{entry[1]}")
    for entry in ALL_FUNCTIONS
]


def _doc(func: Callable[..., Any]) -> str:
    """Return the function's dedented docstring, or an empty string if absent."""
    return inspect.getdoc(func) or ""


def _sections(doc: str) -> dict[str, list[str]]:
    """Split a dedented docstring into {section name: [content lines]}."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in doc.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            current = match.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def _summary(doc: str) -> str:
    """Return the description text that precedes the first section header."""
    lines: list[str] = []
    for line in doc.splitlines():
        if _SECTION_RE.match(line):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _documented_params(doc: str) -> list[tuple[str, str]]:
    """Return ordered (name, description) pairs from the Args section."""
    return [
        (match.group(1), match.group(2).strip())
        for line in _sections(doc).get("Args", [])
        if (match := _PARAM_RE.match(line))
    ]


def _signature_params(func: Callable[..., Any]) -> list[str]:
    """Return the parameter names of func, excluding self/cls."""
    return [name for name in inspect.signature(func).parameters if name not in ("self", "cls")]


def _returns_a_value(func: Callable[..., Any]) -> bool:
    """True if the function is annotated as returning something other than None."""
    annotation = inspect.signature(func).return_annotation
    return annotation is not inspect.Signature.empty and annotation is not None


def _has_explicit_raise(func: Callable[..., Any]) -> bool:
    """True if the function body contains an explicit raise statement."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    return any(isinstance(node, ast.Raise) for node in ast.walk(tree))


@pytest.mark.unit
class TestServiceDocstrings:
    """Test suite for docstring coverage and signature parity in core/services."""

    def test_discovery_finds_every_public_service_function(self) -> None:
        """Test the discovery helper collects the full public service API."""
        found = {name for _, name, _ in ALL_FUNCTIONS}

        missing = EXPECTED_PUBLIC_FUNCTIONS - found
        assert not missing, f"discovery missed public functions: {sorted(missing)}"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_function_has_a_docstring(self, entry: ServiceFunction) -> None:
        """Test every service function has a non-empty docstring."""
        _, name, func = entry

        doc = _doc(func)

        assert doc.strip(), f"{name} has no docstring"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_docstring_opens_with_a_summary_sentence(self, entry: ServiceFunction) -> None:
        """Test the docstring starts with a description, not a bare section."""
        _, name, func = entry

        summary = _summary(_doc(func))

        assert summary, f"{name} has no summary before its first section"
        assert summary.splitlines()[0].endswith(
            "."
        ), f"{name} summary should be a sentence ending in a period"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_args_section_present_when_function_takes_parameters(
        self, entry: ServiceFunction
    ) -> None:
        """Test any function with parameters documents them under Args."""
        _, name, func = entry
        expected = _signature_params(func)

        sections = _sections(_doc(func))

        if expected:
            assert "Args" in sections, f"{name} takes {expected} but has no Args section"
        else:
            assert "Args" not in sections, f"{name} takes no parameters but has an Args section"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_args_document_exactly_the_signature_parameters(self, entry: ServiceFunction) -> None:
        """Test documented parameters match the real signature, with no drift."""
        _, name, func = entry
        expected = set(_signature_params(func))

        documented = {param for param, _ in _documented_params(_doc(func))}

        assert documented == expected, (
            f"{name} Args mismatch: undocumented={sorted(expected - documented)}, "
            f"documented but not a parameter={sorted(documented - expected)}"
        )

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_args_are_documented_in_signature_order(self, entry: ServiceFunction) -> None:
        """Test Args entries are listed in the order the parameters are declared."""
        _, name, func = entry
        expected = _signature_params(func)

        documented = [param for param, _ in _documented_params(_doc(func))]

        assert (
            documented == expected
        ), f"{name} documents parameters as {documented}, signature order is {expected}"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_every_documented_parameter_has_a_description(self, entry: ServiceFunction) -> None:
        """Test no parameter is listed with an empty description."""
        _, name, func = entry

        documented = _documented_params(_doc(func))

        undescribed = [param for param, description in documented if not description]
        assert not undescribed, f"{name} documents {undescribed} with no description"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_returns_documented_when_function_returns_a_value(self, entry: ServiceFunction) -> None:
        """Test functions annotated with a non-None return document Returns."""
        _, name, func = entry

        sections = _sections(_doc(func))

        if _returns_a_value(func):
            assert "Returns" in sections, (
                f"{name} returns {inspect.signature(func).return_annotation} "
                f"but has no Returns section"
            )
            assert any(
                line.strip() for line in sections["Returns"]
            ), f"{name} has an empty Returns section"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_raises_documented_when_function_raises(self, entry: ServiceFunction) -> None:
        """Test functions containing an explicit raise document Raises."""
        _, name, func = entry

        sections = _sections(_doc(func))

        if _has_explicit_raise(func):
            assert (
                "Raises" in sections
            ), f"{name} contains an explicit raise but has no Raises section"
            assert any(
                line.strip() for line in sections["Raises"]
            ), f"{name} has an empty Raises section"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_sections_appear_in_canonical_google_order(self, entry: ServiceFunction) -> None:
        """Test sections are ordered Args, Returns, Raises as Google style expects."""
        _, name, func = entry
        present = [section for section in _sections(_doc(func)) if section in GOOGLE_SECTIONS]

        order = [GOOGLE_SECTIONS.index(section) for section in present]

        assert order == sorted(
            order
        ), f"{name} orders sections as {present}, expected canonical Google order"

    @pytest.mark.parametrize("entry", FUNCTION_CASES)
    def test_docstring_has_no_placeholder_text(self, entry: ServiceFunction) -> None:
        """Test no docstring was left with a TODO or similar placeholder."""
        _, name, func = entry
        doc = _doc(func)

        placeholders = [marker for marker in ("TODO", "FIXME", "XXX", "TBD") if marker in doc]

        assert not placeholders, f"{name} docstring contains {placeholders}"
