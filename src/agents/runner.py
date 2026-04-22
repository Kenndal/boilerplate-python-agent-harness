from dataclasses import dataclass
import logging

from pydantic_ai.exceptions import (
    AgentRunError,
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
    UserError,
)
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import UsageLimits
from result import Err, Ok, Result
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_429_TOO_MANY_REQUESTS,
)

from src.agents.deps import AgentDeps
from src.agents.registry import get_default_agent
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult

logger = logging.getLogger(__name__)


@dataclass
class RunnerOutput:
    """Internal runner return type.

    `input_tokens` / `output_tokens` are kept here purely for server-side persistence and
    observability; the HTTP layer never surfaces them to callers.
    """

    output: str
    new_messages: list[ModelMessage]
    input_tokens: int | None
    output_tokens: int | None


def _map_pai_error(exc: Exception) -> ErrorResult:
    """Translate pydantic-ai and transport exceptions into our ErrorResult taxonomy.

    Keeps higher layers ignorant of provider-specific error types; everything downstream
    pattern-matches on ErrorStatus.
    """
    if isinstance(exc, ModelHTTPError):
        if exc.status_code in {HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN}:
            return ErrorResult(status=ErrorStatus.BAD_REQUEST, details=f"LLM auth error: {exc}")
        if exc.status_code == HTTP_429_TOO_MANY_REQUESTS:
            return ErrorResult(status=ErrorStatus.CONFLICT, details=f"LLM rate limited: {exc}")
        return ErrorResult(
            status=ErrorStatus.INTERNAL_ERROR,
            details=f"LLM HTTP error {exc.status_code}: {exc}",
        )
    if isinstance(exc, UsageLimitExceeded):
        return ErrorResult(status=ErrorStatus.BAD_REQUEST, details=f"Usage limit exceeded: {exc}")
    if isinstance(exc, (UnexpectedModelBehavior, AgentRunError, ModelAPIError, UserError)):
        return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=f"Agent run failed: {exc}")
    if isinstance(exc, TimeoutError):
        return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="LLM request timed out")
    return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=f"Unexpected agent error: {exc}")


class AgentRunner:
    """Thin orchestration layer wrapping `pydantic_ai.Agent.run`.

    Responsibilities:
    - Resolve the single application-wide agent via `get_default_agent`.
    - Run the agent with the caller-supplied `message_history` already hydrated from storage.
    - Normalise provider/timeout/auth errors into our `ErrorResult` taxonomy.
    - Return the newly-produced `ModelMessage`s plus token counts so the conversation service
      can persist them.  Token counts never leave the server boundary.
    """

    async def run(
        self,
        prompt: str,
        history: list[ModelMessage] | None,
        deps: AgentDeps,
        usage_limits: UsageLimits | None = None,
    ) -> Result[RunnerOutput, ErrorResult]:
        agent = get_default_agent()
        try:
            result = await agent.run(
                prompt,
                deps=deps,
                message_history=history,
                usage_limits=usage_limits,
            )
        except Exception as e:
            logger.exception("Agent run failed")
            return Err(_map_pai_error(e))

        usage = result.usage()
        return Ok(
            RunnerOutput(
                output=str(result.output),
                new_messages=list(result.new_messages()),
                input_tokens=getattr(usage, "input_tokens", None),
                output_tokens=getattr(usage, "output_tokens", None),
            )
        )
