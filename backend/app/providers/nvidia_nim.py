from app.config import settings
from app.providers.base import OpenAICompatibleProvider


class NvidiaNimProvider(OpenAICompatibleProvider):
    """NVIDIA NIM expone una API de chat completions compatible con OpenAI."""

    def __init__(self):
        super().__init__(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key,
            model=settings.nvidia_model,
            provider_name="NVIDIA NIM",
        )
