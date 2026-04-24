from unittest.mock import AsyncMock, MagicMock

from pydantic_ai.exceptions import (
    AgentRunError,
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
    UserError,
)
import pytest
from result import Err

from src.agents.deps import AgentDeps
from src.agents.runner import AgentRunner
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult


def _build_runner_with_side_effect(exc: Exception) -> AgentRunner:
    agent = MagicMock()
    agent.run = AsyncMock(side_effect=exc)
    return AgentRunner(agent=agent)


async def _run_with_exception(exc: Exception) -> Err[ErrorResult]:
    runner = _build_runner_with_side_effect(exc)
    result = await runner.run(
        prompt="hello",
        history=None,
        deps=AgentDeps(user_id="u1", user_service=MagicMock()),
    )
    assert isinstance(result, Err)
    return result


async def test_run_maps_unexpected_errors_to_internal_error() -> None:
    result = await _run_with_exception(RuntimeError("tool failed"))
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR
    assert "Unexpected agent error: tool failed" == result.err_value.details


async def test_run_maps_http_auth_errors_to_bad_request() -> None:
    result = await _run_with_exception(
        ModelHTTPError(
            status_code=401,
            model_name="test-model",
            body="unauthorized",
        )
    )
    assert result.err_value.status == ErrorStatus.BAD_REQUEST
    assert "LLM auth error" in result.err_value.details


async def test_run_maps_http_rate_limit_errors_to_conflict() -> None:
    result = await _run_with_exception(
        ModelHTTPError(
            status_code=429,
            model_name="test-model",
            body="rate limited",
        )
    )
    assert result.err_value.status == ErrorStatus.CONFLICT
    assert "LLM rate limited" in result.err_value.details


async def test_run_maps_http_non_auth_errors_to_internal_error() -> None:
    result = await _run_with_exception(
        ModelHTTPError(
            status_code=500,
            model_name="test-model",
            body="provider crash",
        )
    )
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR
    assert "LLM HTTP error 500" in result.err_value.details


async def test_run_maps_timeout_to_internal_error() -> None:
    result = await _run_with_exception(TimeoutError())
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR
    assert result.err_value.details == "LLM request timed out"


@pytest.mark.parametrize(
    "exc",
    [
        UnexpectedModelBehavior("malformed response"),
        AgentRunError("runner failed"),
        ModelAPIError(model_name="test-model", message="api failure"),
        UserError("misconfigured agent"),
    ],
)
async def test_run_maps_known_agent_errors_to_internal_error(exc: Exception) -> None:
    result = await _run_with_exception(exc)
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR
    assert result.err_value.details.startswith("Agent run failed:")


async def test_run_maps_usage_limit_exceeded_to_bad_request() -> None:
    result = await _run_with_exception(UsageLimitExceeded("limit reached"))
    assert result.err_value.status == ErrorStatus.BAD_REQUEST
    assert result.err_value.details.startswith("Usage limit exceeded:")
