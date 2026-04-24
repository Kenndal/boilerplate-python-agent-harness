from unittest.mock import AsyncMock, MagicMock

from pydantic_ai.exceptions import ModelHTTPError
from result import Err

from src.agents.deps import AgentDeps
from src.agents.runner import AgentRunner
from src.models.enums.error_status import ErrorStatus
from src.models.tool_execution_error import ToolExecutionError


def _build_runner_with_side_effect(exc: Exception) -> AgentRunner:
    agent = MagicMock()
    agent.run = AsyncMock(side_effect=exc)
    return AgentRunner(agent=agent)


async def test_run_maps_typed_tool_execution_error() -> None:
    runner = _build_runner_with_side_effect(
        ToolExecutionError(
            tool_name="count_active_users",
            status=ErrorStatus.CONFLICT,
            code="user_service_error",
            message="Failed to fetch active user count from user service",
            details={"service_status": "InternalError"},
        )
    )

    result = await runner.run(
        prompt="hello",
        history=None,
        deps=AgentDeps(user_id="u1", user_service=MagicMock()),
    )

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.CONFLICT
    assert "Tool `count_active_users` failed [user_service_error]" in result.err_value.details


async def test_run_maps_http_auth_errors_to_bad_request() -> None:
    runner = _build_runner_with_side_effect(ModelHTTPError(status_code=401, model_name="test-model", body="unauthorized"))

    result = await runner.run(
        prompt="hello",
        history=None,
        deps=AgentDeps(user_id="u1", user_service=MagicMock()),
    )

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.BAD_REQUEST
    assert "LLM auth error" in result.err_value.details
