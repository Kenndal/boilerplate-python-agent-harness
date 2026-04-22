from dataclasses import dataclass

from src.services.user_service import UserService


@dataclass
class AgentDeps:
    """Per-request dependencies made available to agent tools via pydantic-ai's RunContext.

    Carries the caller identity plus any business services tools may need.  All services here
    share the same AsyncSession / transaction as the request that invoked the agent, so tool
    writes are part of the same atomic unit of work as the surrounding HTTP request.

    Extend this as the agent harness grows (add more services, an auth context, etc.).
    """

    user_id: str
    user_service: UserService
