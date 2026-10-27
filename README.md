# MCP Tool Integration

A Python MCP server that exposes workspace files and SQLite metadata as resources, and registers validated tools for safe database queries and workspace operations.

## Features

- Official Python MCP SDK with stdio transport and initialization lifecycle.
- `file://workspace/...` resources and a URI template for workspace files.
- `db://schema` and `db://table/{name}` resources.
- Pydantic v2 validation for tool inputs and JSON-RPC `-32602` errors for invalid parameters.
- Read-only SQLite query execution, schema inspection, and bounded result sets.
- Workspace path validation against traversal, absolute paths, and symlinks.
- Safe workspace file creation and overwrite confirmation.
- MCP prompts, an end-to-end client harness, and automated tests.

## Run

Python 3.10 or newer is required.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install and verify:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python scripts/test_client.py
```

Start the server directly:

```bash
python -m mcp_tool_integration.server
```

The server communicates over stdio. Use an MCP host/client to connect to it; do not type commands into the server process's stdin.

## Resources

| URI | Purpose |
| --- | --- |
| `file://workspace/notes.md` | Example workspace document |
| `file://workspace/{relative_path}` | Workspace file resource template |
| `db://schema` | Database table and view names |
| `db://table/users` | Column metadata for the `users` table |

## Tools

- `execute_safe_query`: one read-only `SELECT`/`WITH` query, with bounded rows.
- `get_database_schema`: list tables or inspect a table's columns.
- `list_workspace_files`: list files beneath the configured workspace root.
- `read_workspace_file`: read a UTF-8 file using a workspace-relative path.
- `write_workspace_file`: create a file or overwrite one after explicit approval.

Before setting `confirm_overwrite=true`, the MCP host should obtain approval from the user. The server still restricts the target to the configured workspace.

## Configuration

By default, the workspace is `workspace/` and the database is `data/app.db` in the project directory. Override either location with environment variables:

- `MCP_WORKSPACE`
- `MCP_DATABASE`

The database and its sample tables are initialized when the server starts.

## Verification

`python -m pytest -q` runs unit and stdio integration tests. `python scripts/test_client.py` performs an end-to-end handshake, checks resource/template and prompt discovery, reads resources, executes a safe query, verifies validation/security failures, and exercises file-write confirmation. On success, it writes `reports/verification.json`.

## Security boundaries

- SQL runs through a read-only SQLite connection and accepts a single query statement.
- File paths are resolved against the configured workspace root. Traversal, absolute paths, and symlinks are rejected.
- Files larger than 1 MB are not exposed as resources; writes are limited to 200 KB.
- Errors are returned through MCP/JSON-RPC without returning internal exception traces.
- The host application remains responsible for policy decisions and user approval for writes.
