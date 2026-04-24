from dataclasses import dataclass, field
from typing import Any

from src.models.enums.error_status import ErrorStatus


@dataclass(slots=True)
class ToolExecutionError(Exception):
    """Typed exception for tool failures with structured diagnostics."""

    tool_name: str
    status: ErrorStatus
    message: str
    code: str = "tool_execution_failed"
    details: dict[str, Any] = field(default_factory=dict)

    def to_error_details(self) -> str:
        return f"Tool `{self.tool_name}` failed [{self.code}]: {self.message}"
