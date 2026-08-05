"""Structural tests for public service docstrings."""

import ast
from pathlib import Path

import pytest

SERVICE_DIR = Path("core/services")


def _public_functions(path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return public top-level functions declared in a Python module."""
    tree = ast.parse(path.read_text())
    return [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    ]


@pytest.mark.unit
def test_public_service_functions_have_google_style_docstrings() -> None:
    """Require descriptions and contract sections on public services."""
    discovered = 0

    for path in sorted(SERVICE_DIR.glob("*.py")):
        for function in _public_functions(path):
            discovered += 1
            docstring = ast.get_docstring(function)
            qualified_name = f"{path.name}:{function.name}"

            assert docstring, f"{qualified_name} has no docstring"
            assert docstring.splitlines()[0].strip(), f"{qualified_name} has no summary description"
            assert "\nArgs:" in docstring, f"{qualified_name} has no Args section"
            assert "\nReturns:" in docstring, f"{qualified_name} has no Returns section"
            assert "\nRaises:" in docstring, f"{qualified_name} has no Raises section"

    assert discovered == 8, f"expected 8 public service functions, found {discovered}"
