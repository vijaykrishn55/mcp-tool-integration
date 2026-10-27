"""Strict input models for MCP tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Annotated

SafeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
RelativePath = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=400)]
SqlText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
FileText = Annotated[str, StringConstraints(max_length=200_000)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)


class ExecuteSafeQueryInput(StrictInput):
    query: SqlText = Field(description="A single read-only SELECT query.")
    max_rows: int = Field(default=100, ge=1, le=500, description="Maximum rows returned.")


class ReadWorkspaceFileInput(StrictInput):
    relative_path: RelativePath = Field(description="Path relative to the designated workspace root.")


class ListWorkspaceFilesInput(StrictInput):
    subdirectory: str = Field(default="", max_length=400, description="Optional workspace-relative directory.")


class WriteWorkspaceFileInput(StrictInput):
    relative_path: RelativePath = Field(description="Path relative to the designated workspace root.")
    content: FileText = Field(description="Content to write to the file.")
    confirm_overwrite: bool = Field(
        default=False,
        description="Must be true to replace an existing regular file. The host should obtain user confirmation first.",
    )


class TableSchemaInput(StrictInput):
    table_name: SafeName | None = Field(default=None, description="Optional table name. Omit it to list all tables.")
