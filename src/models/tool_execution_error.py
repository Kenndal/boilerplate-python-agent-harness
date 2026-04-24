from typing import Any

from pydantic import BaseModel, Field

from src.models.enums.error_status import ErrorStatus


class ToolExecutionError(BaseModel):
    """Typed exception for tool failures with structured diagnostics."""

    tool_name: str
    status: ErrorStatus
    message: str
    code: str = "tool_execution_failed"
    details: dict[str, Any] = Field(default_factory=dict)

    @property
    def error_details(self) -> str:
        return f"Tool `{self.tool_name}` failed [{self.status.value}][{self.code}]: {self.message}"

    def __str__(self) -> str:
        return self.error_details
