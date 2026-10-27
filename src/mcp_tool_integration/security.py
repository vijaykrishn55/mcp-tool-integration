"""Workspace path and SQL safety checks."""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit


class AccessDeniedError(PermissionError):
    """Raised when a requested path leaves the configured workspace."""


class InvalidRequestError(ValueError):
    """Raised when a requested path or SQL statement violates policy."""


def resolve_workspace_path(workspace_root: Path, user_path: str) -> Path:
    """Resolve a relative file path, rejecting traversal and symlink escapes."""
    if not isinstance(user_path, str) or not user_path.strip():
        raise InvalidRequestError("A non-empty relative path is required.")

    decoded = unquote(user_path).replace("\\", "/").strip()
    if "\x00" in decoded:
        raise InvalidRequestError("Null bytes are not allowed in paths.")

    # Do not accept absolute POSIX or Windows paths, including drive-relative paths.
    if decoded.startswith("/") or PureWindowsPath(decoded).is_absolute() or PureWindowsPath(decoded).drive:
        raise AccessDeniedError("Absolute paths are not allowed. Use a workspace-relative path.")

    segments = decoded.split("/")
    if any(segment == ".." for segment in segments):
        raise AccessDeniedError("Path traversal is not allowed.")

    root = workspace_root.resolve()
    target = (root / Path(*[s for s in segments if s not in ("", ".")])).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AccessDeniedError("Access denied: path resolves outside the workspace.") from exc

    # Reject symlinks anywhere in an existing path, even if their target happens to be inside root.
    cursor = root
    for segment in [s for s in segments if s not in ("", ".")]:
        cursor = cursor / segment
        if cursor.is_symlink():
            raise AccessDeniedError("Symbolic links are not permitted in workspace paths.")

    return target


def path_from_resource_uri(uri: str, workspace_root: Path) -> Path:
    parsed = urlsplit(str(uri))
    if parsed.scheme != "file" or parsed.netloc != "workspace":
        raise InvalidRequestError(f"Unsupported resource URI: {uri}")
    relative = unquote(parsed.path).lstrip("/")
    return resolve_workspace_path(workspace_root, relative)


def normalize_readonly_sql(query: str) -> str:
    """Allow exactly one SELECT statement; read-only DB mode is the second defense."""
    if not isinstance(query, str) or not query.strip():
        raise InvalidRequestError("SQL query must not be empty.")

    # Strip leading comments so they cannot be used to hide a non-SELECT statement.
    sql = query.strip()
    while True:
        stripped = re.sub(r"^\s*(?:--[^\n]*(?:\n|$)|/\*.*?\*/\s*)", "", sql, count=1, flags=re.DOTALL)
        if stripped == sql:
            break
        sql = stripped
    if not sql:
        raise InvalidRequestError("SQL query must not be empty.")

    # A single trailing semicolon is accepted; any remaining semicolon can indicate multiple statements.
    sql = sql.rstrip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    if ";" in sql:
        raise InvalidRequestError("Only one SQL statement is allowed.")

    first_keyword = re.match(r"([A-Za-z]+)", sql)
    if not first_keyword or first_keyword.group(1).upper() not in {"SELECT", "WITH"}:
        raise InvalidRequestError("Only read-only SELECT queries are allowed.")

    # Block known mutation verbs even if hidden in a WITH clause. SQLite read-only mode remains authoritative.
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH|DETACH|VACUUM|REINDEX|PRAGMA)\b",
        re.IGNORECASE,
    )
    if forbidden.search(sql):
        raise InvalidRequestError("The query contains a forbidden SQL operation.")
    return sql
