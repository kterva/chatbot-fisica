from app.config import settings
from app.providers.base import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter expone una API de chat completions compatible con OpenAI."""

    def __init__(self):
        super().__init__(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            provider_name="OpenRouter",
        )
