import pytest
from pydantic import ValidationError

from mcp_tool_integration.models import ExecuteSafeQueryInput, WriteWorkspaceFileInput


def test_query_model_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ExecuteSafeQueryInput.model_validate({"query": "SELECT 1", "admin": True})


def test_query_model_rejects_coerced_integer():
    with pytest.raises(ValidationError):
        ExecuteSafeQueryInput.model_validate({"query": "SELECT 1", "max_rows": "5"})


def test_write_model_requires_explicit_confirmation_flag_type():
    with pytest.raises(ValidationError):
        WriteWorkspaceFileInput.model_validate({
            "relative_path": "notes.txt",
            "content": "hello",
            "confirm_overwrite": "yes",
        })
