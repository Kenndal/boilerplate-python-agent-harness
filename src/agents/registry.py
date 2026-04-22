from typing import Any

from pydantic_ai import Agent

from src.agents.deps import AgentDeps
from src.agents.sample.agent import sample_agent


def get_default_agent() -> Agent[AgentDeps, Any]:
    """Return the single application-wide agent.

    The HTTP surface intentionally exposes one agent only, so this function is the single
    place that decides which `pydantic_ai.Agent` instance backs every conversation.
    """
    return sample_agent
