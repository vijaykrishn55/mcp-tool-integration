import asyncio
from pathlib import Path

import pytest

from mcp_tool_integration.database import execute_readonly_query, initialize_database, read_schema
from mcp_tool_integration.security import InvalidRequestError


@pytest.mark.asyncio
async def test_database_seed_and_readonly_query(tmp_path: Path):
    db_path = tmp_path / "test.db"
    await initialize_database(db_path)
    result = await execute_readonly_query(db_path, "SELECT name, role FROM users ORDER BY id")
    assert result["row_count"] == 2
    assert result["rows"][0]["name"] == "Alice Smith"
    schema = await read_schema(db_path)
    assert {table["name"] for table in schema["tables"]} >= {"users", "projects"}


@pytest.mark.asyncio
async def test_readonly_connection_prevents_writes(tmp_path: Path):
    db_path = tmp_path / "test.db"
    await initialize_database(db_path)
    with pytest.raises(InvalidRequestError):
        await execute_readonly_query(db_path, "DROP TABLE users")
    result = await execute_readonly_query(db_path, "SELECT COUNT(*) AS n FROM users")
    assert result["rows"][0]["n"] == 2
