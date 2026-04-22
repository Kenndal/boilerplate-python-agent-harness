from pydantic_ai import RunContext
from result import Err, Ok

from src.agents.deps import AgentDeps


async def count_active_users(ctx: RunContext[AgentDeps]) -> int:
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
            raise RuntimeError(error.details)
        case _:
            raise RuntimeError("Unexpected result from user service")
