import logging
from uuid import UUID

from result import Err, Ok, Result

from src.agents.deps import AgentDeps
from src.agents.messages_history_helpers import model_messages_to_creates, rows_to_model_messages
from src.agents.runner import AgentRunner, RunnerOutput
from src.config.config import config
from src.models.agent import AgentMessage, AgentTurnResponse
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.agent_message_service import AgentMessageService
from src.services.agent_session_service import AgentSessionService

logger = logging.getLogger(__name__)


class AgentConversationService:
    """Composition service that orchestrates a single agent turn.

    Flow:
      1. Authorise the caller against the session.
      2. Load persisted messages and hydrate them back into pydantic-ai `ModelMessage`s.
         When the history exceeds `max_history_messages`, only the tail is fed to the LLM
         (older turns remain on disk for display but are dropped from the context window).
      3. Invoke the agent with that history plus the new prompt.
      4. Persist every message produced by the run (user prompt + assistant + tools) with
         monotonic sequence numbers; token counts attach to the final assistant row.
      5. Return `AgentTurnResponse` with the freshly persisted rows.  Usage is intentionally
         not returned to the caller.
    """

    def __init__(
        self,
        session_service: AgentSessionService,
        message_service: AgentMessageService,
        runner: AgentRunner,
        max_history_messages: int | None = None,
    ) -> None:
        self.session_service = session_service
        self.message_service = message_service
        self.runner = runner
        self.max_history_messages = (
            max_history_messages if max_history_messages is not None else config.AGENT_MAX_HISTORY_MESSAGES
        )

    async def send_message(
        self,
        session_id: UUID,
        prompt: str,
        user_id: str,
        agent_deps: AgentDeps,
    ) -> Result[AgentTurnResponse, ErrorResult]:
        match await self.session_service.get_session_by_id_for_user(session_id, user_id):
            case Err(error):
                return Err(error)
            case Ok(_):
                pass
            case _:
                return Err(
                    ErrorResult(
                        status=ErrorStatus.INTERNAL_ERROR,
                        details="Unexpected session lookup result",
                    )
                )

        match await self.message_service.list_for_session(session_id):
            case Err(error):
                return Err(error)
            case Ok(messages):
                history = rows_to_model_messages(self._clip_history(messages))
            case _:
                return Err(
                    ErrorResult(
                        status=ErrorStatus.INTERNAL_ERROR,
                        details="Unexpected history lookup result",
                    )
                )

        match await self.runner.run(prompt=prompt, history=history or None, deps=agent_deps):
            case Err(error):
                return Err(error)
            case Ok(runner_output):
                return await self._persist_runner_output(session_id, user_id, runner_output)
            case _:
                return Err(
                    ErrorResult(
                        status=ErrorStatus.INTERNAL_ERROR,
                        details="Unexpected runner result",
                    )
                )

    def _clip_history(self, rows: list) -> list:  # type: ignore[type-arg]
        if self.max_history_messages <= 0 or len(rows) <= self.max_history_messages:
            return rows
        return rows[-self.max_history_messages :]

    async def _persist_runner_output(
        self,
        session_id: UUID,
        user_id: str,
        runner_output: RunnerOutput,
    ) -> Result[AgentTurnResponse, ErrorResult]:
        match await self.message_service.max_sequence(session_id):
            case Err(error):
                return Err(error)
            case Ok(last_sequence):
                start_sequence = last_sequence + 1
            case _:
                return Err(
                    ErrorResult(
                        status=ErrorStatus.INTERNAL_ERROR,
                        details="Unexpected max_sequence result",
                    )
                )

        creates = model_messages_to_creates(
            messages=runner_output.new_messages,
            session_id=session_id,
            start_sequence=start_sequence,
            input_tokens=runner_output.input_tokens,
            output_tokens=runner_output.output_tokens,
        )

        if not creates:
            return Ok(AgentTurnResponse(output=runner_output.output, new_messages=[]))

        match await self.message_service.append_many(creates=creates, user_id=user_id):
            case Err(error):
                return Err(error)
            case Ok(persisted):
                return Ok(
                    AgentTurnResponse(
                        output=runner_output.output,
                        new_messages=[AgentMessage.model_validate(m.model_dump()) for m in persisted],
                    )
                )
            case _:
                return Err(
                    ErrorResult(
                        status=ErrorStatus.INTERNAL_ERROR,
                        details="Unexpected append_many result",
                    )
                )
