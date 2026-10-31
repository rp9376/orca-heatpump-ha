"""The client package stays independent of Home Assistant (ADR 0003)."""

import ast
from pathlib import Path

import pytest

CLIENT_DIR = (
    Path(__file__).parents[2] / "custom_components" / "orca_heatpump" / "client"
)


def _foreign_imports(path: Path) -> list[str]:
    """Return imports that reach Home Assistant or outside the client package."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    depth = len(path.relative_to(CLIENT_DIR).parts)
    foreign: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            foreign.extend(
                alias.name
                for alias in node.names
                if alias.name.partition(".")[0] == "homeassistant"
            )
        elif isinstance(node, ast.ImportFrom):
            if node.level > depth:
                foreign.append("." * node.level + (node.module or ""))
            elif node.level == 0 and (node.module or "").partition(".")[0] in (
                "homeassistant",
                "custom_components",
            ):
                foreign.append(node.module or "")
    return foreign


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(path, id=path.relative_to(CLIENT_DIR).as_posix())
        for path in sorted(CLIENT_DIR.rglob("*.py"))
    ],
)
def test_client_imports_nothing_from_home_assistant(path: Path) -> None:
    """Client modules import neither Home Assistant nor the integration."""
    assert _foreign_imports(path) == []
