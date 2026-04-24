from unittest.mock import AsyncMock, MagicMock

from pydantic_ai.exceptions import ModelHTTPError
from result import Err

from src.agents.deps import AgentDeps
from src.agents.runner import AgentRunner
from src.models.enums.error_status import ErrorStatus


def _build_runner_with_side_effect(exc: Exception) -> AgentRunner:
    agent = MagicMock()
    agent.run = AsyncMock(side_effect=exc)
    return AgentRunner(agent=agent)


async def test_run_maps_unexpected_errors_to_internal_error() -> None:
    runner = _build_runner_with_side_effect(RuntimeError("tool failed"))

    result = await runner.run(
        prompt="hello",
        history=None,
        deps=AgentDeps(user_id="u1", user_service=MagicMock()),
    )

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR
    assert "Unexpected agent error: tool failed" == result.err_value.details


async def test_run_maps_http_auth_errors_to_bad_request() -> None:
    runner = _build_runner_with_side_effect(
        ModelHTTPError(status_code=401, model_name="test-model", body="unauthorized")
    )

    result = await runner.run(
        prompt="hello",
        history=None,
        deps=AgentDeps(user_id="u1", user_service=MagicMock()),
    )

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.BAD_REQUEST
    assert "LLM auth error" in result.err_value.details
