from pathlib import Path

import pytest

from mcp_tool_integration.security import (
    AccessDeniedError,
    InvalidRequestError,
    normalize_readonly_sql,
    resolve_workspace_path,
)


def test_workspace_relative_path_resolves_inside_root(tmp_path: Path):
    (tmp_path / "notes.md").write_text("hello", encoding="utf-8")
    assert resolve_workspace_path(tmp_path, "notes.md") == (tmp_path / "notes.md").resolve()


@pytest.mark.parametrize("path", ["../secret.txt", "../../etc/passwd", "%2e%2e/%2e%2e/etc/passwd", "C:\\Windows\\win.ini", "/etc/passwd"])
def test_path_traversal_and_absolute_paths_are_denied(tmp_path: Path, path: str):
    with pytest.raises(AccessDeniedError):
        resolve_workspace_path(tmp_path, path)


def test_symlinks_are_rejected(tmp_path: Path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "alias.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this platform.")
    with pytest.raises(AccessDeniedError):
        resolve_workspace_path(tmp_path, "alias.txt")


@pytest.mark.parametrize("sql", ["DROP TABLE users;", "DELETE FROM users", "SELECT 1; DELETE FROM users", "WITH gone AS (SELECT 1) DELETE FROM users"])
def test_mutating_or_multi_statement_sql_is_rejected(sql: str):
    with pytest.raises(InvalidRequestError):
        normalize_readonly_sql(sql)


def test_select_query_is_allowed():
    assert normalize_readonly_sql("SELECT sqlite_version();") == "SELECT sqlite_version()"
