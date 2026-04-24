from pydantic_ai import Agent
from pydantic_ai.models import Model

from src.agents.deps import AgentDeps
from src.agents.sample.prompts import SYSTEM_PROMPT
from src.agents.tools.user_tools import count_active_users


def build_sample_agent(model: Model) -> Agent[AgentDeps, str]:
    agent: Agent[AgentDeps, str] = Agent(
        model=model,
        deps_type=AgentDeps,
        output_type=str,
        system_prompt=SYSTEM_PROMPT,
    )
    agent.tool(count_active_users)
    return agent
