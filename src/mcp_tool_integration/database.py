"""Asynchronous SQLite setup and safe query helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite

from .security import InvalidRequestError, normalize_readonly_sql


async def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(database_path)) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, role TEXT NOT NULL)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS projects ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL UNIQUE, status TEXT NOT NULL)"
        )
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO users(name, role) VALUES (?, ?)",
                [("Alice Smith", "Engineer"), ("Bob Jones", "Product Manager")],
            )
        cursor = await db.execute("SELECT COUNT(*) FROM projects")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO projects(name, status) VALUES (?, ?)",
                [("MCP Integration", "active"), ("Workspace Search", "planned")],
            )
        await db.commit()


def _sqlite_readonly_uri(database_path: Path) -> str:
    # Path.as_uri handles spaces and Windows drive letters correctly.
    # SQLite URI `mode=ro` enforces read-only access at the database engine layer.
    return f"{database_path.resolve().as_uri()}?mode=ro"


async def execute_readonly_query(database_path: Path, query: str, max_rows: int = 100) -> dict[str, Any]:
    sql = normalize_readonly_sql(query)
    if not 1 <= max_rows <= 500:
        raise InvalidRequestError("max_rows must be between 1 and 500.")

    async with aiosqlite.connect(_sqlite_readonly_uri(database_path), uri=True) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA query_only = ON")
        cursor = await db.execute(sql)
        column_names = [column[0] for column in (cursor.description or [])]
        rows = await cursor.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        values = [{key: row[key] for key in column_names} for row in rows]
        return {
            "columns": column_names,
            "rows": values,
            "row_count": len(values),
            "truncated": truncated,
        }


async def read_schema(database_path: Path, table_name: str | None = None) -> dict[str, Any]:
    async with aiosqlite.connect(_sqlite_readonly_uri(database_path), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [dict(row) for row in await cursor.fetchall()]
        if table_name is None:
            return {"tables": tables}

        valid_names = {item["name"] for item in tables}
        if table_name not in valid_names:
            raise InvalidRequestError(f"Unknown table: {table_name}")
        # Table names cannot be bound as parameters. Only quote after exact membership validation.
        escaped = table_name.replace('"', '""')
        cursor = await db.execute(f'PRAGMA table_info("{escaped}")')
        columns = [dict(row) for row in await cursor.fetchall()]
        return {"table": table_name, "columns": columns}


def to_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)
