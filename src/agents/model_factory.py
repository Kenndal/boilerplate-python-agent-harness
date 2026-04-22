import httpx
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.config.config import config


def build_openrouter_model(model_name: str | None = None) -> OpenAIChatModel:
    """Build an OpenAI-compatible chat model pointed at OpenRouter.

    OpenRouter accepts optional attribution headers (HTTP-Referer / X-Title); we wire them
    in only when set so they are visible in the OpenRouter dashboard without leaking defaults.
    """
    headers: dict[str, str] = {}
    if config.LLM_HTTP_REFERER:
        headers["HTTP-Referer"] = config.LLM_HTTP_REFERER
    if config.LLM_APP_TITLE:
        headers["X-Title"] = config.LLM_APP_TITLE

    http_client = httpx.AsyncClient(
        timeout=config.LLM_REQUEST_TIMEOUT_S,
        headers=headers or None,
    )

    provider = OpenAIProvider(
        base_url=config.OPENROUTER_BASE_URL,
        api_key=config.OPENROUTER_API_KEY.get_secret_value(),
        http_client=http_client,
    )
    return OpenAIChatModel(model_name or config.LLM_DEFAULT_MODEL, provider=provider)
