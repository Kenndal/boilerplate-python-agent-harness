from pydantic_ai import Agent

from src.agents.deps import AgentDeps
from src.agents.model_factory import build_openrouter_model
from src.agents.sample.prompts import SYSTEM_PROMPT
from src.agents.tools.user_tools import count_active_users

sample_agent: Agent[AgentDeps, str] = Agent(
    model=build_openrouter_model(),
    deps_type=AgentDeps,
    output_type=str,
    system_prompt=SYSTEM_PROMPT,
)

sample_agent.tool(count_active_users)
