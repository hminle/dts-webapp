"""Methodology guides for agents, with facts filled in from the code at read time.

A skill's prose explains how to get a number with the MCP tools. Anything the
code already knows (the schema, category line items, worked-example numbers) is
a ``{{...}}`` placeholder instead of a copy, so a guide can't drift from the
app. ``worked-examples.json`` here is a copy of the frontend file, because the
Vercel backend bundle has no ``frontend/``; ``test_mcp_skills.py`` keeps the two
identical.
"""

import functools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from app.constants.categories import CATEGORY_REGISTRY
from app.core.config import get_settings
from app.services import sql as sql_service

SKILLS_DIR = Path(__file__).parent / "skills"
EXAMPLES_PATH = Path(__file__).parent / "worked-examples.json"

_MAX_DESCRIPTION = 160
_PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}")
_SCHEMA_SQL = (
    "SELECT table_name, column_name, data_type FROM information_schema.columns "
    "WHERE table_schema = 'main' ORDER BY table_name, ordinal_position"
)


class SkillError(ValueError):
    """A skill file is malformed, or a placeholder does not resolve."""


@dataclass(frozen=True)
class SkillFile:
    name: str
    description: str
    formulas: tuple[str, ...]
    # Raw, placeholders unrendered.
    body: str


def _parse(path: Path) -> SkillFile:
    # Three flat keys; a YAML dependency isn't worth it.
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        raise SkillError(f"{path.name}: must start with a --- frontmatter line")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise SkillError(f"{path.name}: frontmatter is not closed with ---") from exc
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(": ")
        if not sep:
            raise SkillError(f"{path.name}: bad frontmatter line {line!r}")
        fields[key] = value.strip()
    missing = {"name", "description", "formulas"} - set(fields)
    if missing:
        raise SkillError(f"{path.name}: frontmatter is missing {sorted(missing)}")
    if fields["name"] != path.stem:
        raise SkillError(f"{path.name}: name {fields['name']!r} must be {path.stem!r}")
    description = fields["description"]
    if not description or len(description) > _MAX_DESCRIPTION:
        raise SkillError(
            f"{path.name}: description must be 1 to {_MAX_DESCRIPTION} characters"
        )
    raw = fields["formulas"]
    if not (raw.startswith("[") and raw.endswith("]")):
        raise SkillError(f"{path.name}: formulas must be a [bracketed, list]")
    formulas = tuple(f.strip() for f in raw[1:-1].split(",") if f.strip())
    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    return SkillFile(fields["name"], description, formulas, body)


@functools.cache
def load_skills() -> dict[str, SkillFile]:
    """Every skill in ``SKILLS_DIR``, by name, sorted.

    Raises:
        SkillError: A file's frontmatter is missing, unclosed or invalid.
    """
    return {p.stem: _parse(p) for p in sorted(SKILLS_DIR.glob("*.md"))}


@functools.cache
def _examples() -> dict[str, Any]:
    return json.loads(EXAMPLES_PATH.read_text())


def _render_schema(cur: duckdb.DuckDBPyConnection) -> str:
    result = sql_service.run_select(
        cur, _SCHEMA_SQL, max_rows=get_settings().query_max_rows
    )
    tables: dict[str, list[tuple[str, str]]] = {}
    for table, column, data_type in result.rows:
        tables.setdefault(table, []).append((column, data_type))
    sections = []
    for table, columns in tables.items():
        rows = "\n".join(f"| {c} | {t} |" for c, t in columns)
        sections.append(f"### {table}\n\n| column | type |\n|---|---|\n{rows}")
    return "\n\n".join(sections)


def _render_categories() -> str:
    sections = []
    for cat in CATEGORY_REGISTRY.values():
        items = "\n".join(f"- {c}" for c in cat.components)
        sections.append(
            f"### {cat.name}\n\nKind: {cat.kind}\n\n"
            f"Comparable from: {cat.available_from.isoformat()}\n\n{items}"
        )
    return "\n\n".join(sections)


def _render_example(path: str) -> str:
    node: Any = _examples()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SkillError(f"No worked example at {path!r}")
        node = node[part]
    if isinstance(node, dict | list):
        raise SkillError(f"Worked example {path!r} is not a single value")
    # Amounts get thousands separators; a year is a label, not an amount.
    if isinstance(node, int | float) and not isinstance(node, bool):
        return str(node) if part.endswith("year") else f"{node:,}"
    return str(node)


def render(body: str, cur: duckdb.DuckDBPyConnection) -> str:
    """Fill every placeholder in ``body``.

    Raises:
        SkillError: A placeholder is unknown or its example path doesn't resolve.
    """

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token == "schema":
            return _render_schema(cur)
        if token == "categories":
            return _render_categories()
        if token.startswith("example:"):
            return _render_example(token.removeprefix("example:"))
        raise SkillError(f"Unknown placeholder {{{{{token}}}}}")

    return _PLACEHOLDER.sub(replace, body)
