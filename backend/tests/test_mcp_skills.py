"""The MCP skills: frontmatter, placeholders, drift checks, and the tool."""

import re
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.core.duckdb import get_connection
from app.mcp_server import skills
from app.mcp_server.skills import SkillError, load_skills, render
from app.services.sql import run_select

REPO = Path(__file__).resolve().parents[2]
FORMULAS_TS = REPO / "frontend/src/features/methodology/formulas.ts"
FRONTEND_EXAMPLES = REPO / "frontend/src/features/methodology/worked-examples.json"
SQL_BLOCK = re.compile(r"```sql\n(.*?)```", re.DOTALL)

SQL_BLOCKS = [
    pytest.param(block, id=f"{name}-{n}")
    for name, skill in load_skills().items()
    for n, block in enumerate(SQL_BLOCK.findall(skill.body), start=1)
]


@pytest.fixture
def cur(client: TestClient) -> Iterator[duckdb.DuckDBPyConnection]:
    cursor = get_connection().cursor()
    yield cursor
    cursor.close()


def test_skill_names() -> None:
    assert set(load_skills()) == {
        "start-here",
        "data-model",
        "net-transfers",
        "year-over-year",
        "categories",
    }


def test_frontmatter_formulas_exist() -> None:
    source = FORMULAS_TS.read_text()
    for skill in load_skills().values():
        for formula in skill.formulas:
            assert f"id: '{formula}'" in source, f"{skill.name}: {formula}"


def test_worked_examples_copy_matches_frontend() -> None:
    assert skills.EXAMPLES_PATH.read_bytes() == FRONTEND_EXAMPLES.read_bytes(), (
        "The backend copy of worked-examples.json is stale. Run: cp "
        "frontend/src/features/methodology/worked-examples.json "
        "backend/app/mcp_server/worked-examples.json"
    )


@pytest.mark.parametrize("name", sorted(load_skills()))
def test_every_skill_renders(name: str, cur: duckdb.DuckDBPyConnection) -> None:
    rendered = render(load_skills()[name].body, cur)
    assert "{{" not in rendered


def test_schema_placeholder_lists_tables(cur: duckdb.DuckDBPyConnection) -> None:
    rendered = render(load_skills()["data-model"].body, cur)
    for table in ("deposits_withdrawals", "daily_net_transfers", "metadata"):
        assert f"### {table}" in rendered


def test_categories_placeholder(cur: duckdb.DuckDBPyConnection) -> None:
    rendered = render(load_skills()["categories"].body, cur)
    assert "### Medicare" in rendered
    assert "HHS - Medicare Prescription Drugs" in rendered


def test_example_placeholder(cur: duckdb.DuckDBPyConnection) -> None:
    rendered = render("{{example:net_transfers.outputs.fytd.net_transfers}}", cur)
    assert rendered == "108,932"


@pytest.mark.parametrize(
    "body", ["{{nope}}", "{{example:no.such.path}}", "{{example:net_transfers}}"]
)
def test_unknown_placeholder(body: str, cur: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(SkillError):
        render(body, cur)


@pytest.mark.parametrize("sql", SQL_BLOCKS)
def test_skill_sql_runs(sql: str, cur: duckdb.DuckDBPyConnection) -> None:
    run_select(cur, sql)


def test_bad_frontmatter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "wrong.md").write_text(
        "---\nname: right\ndescription: x\nformulas: []\n---\nbody\n"
    )
    monkeypatch.setattr(skills, "SKILLS_DIR", tmp_path)
    load_skills.cache_clear()
    try:
        with pytest.raises(SkillError, match="wrong.md"):
            load_skills()
    finally:
        load_skills.cache_clear()


async def test_get_skills_tool(mcp_client: Client) -> None:
    listed = await mcp_client.call_tool("get_skills", {})
    assert len(listed.data) == 5

    skill = await mcp_client.call_tool("get_skills", {"name": "net-transfers"})
    assert "108,932" in skill.data.body

    with pytest.raises(ToolError, match="Available: categories"):
        await mcp_client.call_tool("get_skills", {"name": "nope"})
