from unittest.mock import AsyncMock

from pydantic_ai.messages import ModelRequest, ToolReturnPart
from pydantic_ai.models.test import TestModel
from result import Err, Ok

from src.agents.deps import AgentDeps
from src.agents.sample.agent import build_sample_agent
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.models.tool_execution_error import ToolExecutionError


async def test_sample_agent_uses_count_active_users_tool_on_success() -> None:
    user_service = AsyncMock()
    user_service.get_page = AsyncMock(return_value=Ok(ModelList(items=[], total=7)))
    agent = build_sample_agent(model=TestModel(call_tools="all"))

    result = await agent.run(
        user_prompt="How many active users are there?",
        deps=AgentDeps(user_id="u1", user_service=user_service),
    )

    user_service.get_page.assert_awaited_once()
    assert result.output == '{"count_active_users":7}'


async def test_sample_agent_surfaces_structured_tool_error_payload() -> None:
    user_service = AsyncMock()
    user_service.get_page = AsyncMock(
        return_value=Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="db down"))
    )
    agent = build_sample_agent(model=TestModel(call_tools="all"))

    result = await agent.run(
        user_prompt="How many active users are there?",
        deps=AgentDeps(user_id="u1", user_service=user_service),
    )

    tool_return_parts = [
        part
        for message in result.new_messages()
        if isinstance(message, ModelRequest)
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]
    assert len(tool_return_parts) == 1
    tool_payload = tool_return_parts[0].content
    assert isinstance(tool_payload, ToolExecutionError)
    assert tool_payload.tool_name == "count_active_users"
    assert tool_payload.code == "user_service_error"
    assert tool_payload.status == ErrorStatus.INTERNAL_ERROR
    assert tool_payload.details["service_status"] == ErrorStatus.INTERNAL_ERROR.value
    assert tool_payload.details["service_details"] == "db down"
    assert "count_active_users" in result.output
