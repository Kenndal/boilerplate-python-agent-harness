from pydantic_ai import RunContext
from result import Err, Ok

from src.agents.deps import AgentDeps
from src.models.enums.error_status import ErrorStatus
from src.models.tool_execution_error import ToolExecutionError


async def count_active_users(ctx: RunContext[AgentDeps]) -> int | ToolExecutionError:
    """Return the number of active users currently in the system.

    Implemented as a thin wrapper over UserService.get_page so all DB access stays in the
    service layer and inside the request-scoped transaction.
    """
    match await ctx.deps.user_service.get_page(
        page_number=1,
        page_size=1,
        omit_pagination=False,
        is_active=True,
    ):
        case Ok(page):
            return page.total
        case Err(error):
            return ToolExecutionError(
                tool_name="count_active_users",
                status=error.status,
                code="user_service_error",
                message=f"Failed to fetch active user count from user service, {error.details}",
                details={
                    "service_status": error.status.value,
                    "service_details": error.details,
                },
            )
        case _:
            return ToolExecutionError(
                tool_name="count_active_users",
                status=ErrorStatus.INTERNAL_ERROR,
                code="unexpected_result",
                message="User service returned an unsupported result shape",
            )
