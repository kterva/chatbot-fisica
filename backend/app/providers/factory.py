from app.config import settings
from app.providers.base import LLMProvider
from app.providers.gemini import GeminiProvider
from app.providers.nvidia_nim import NvidiaNimProvider
from app.providers.openrouter import OpenRouterProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "nvidia": NvidiaNimProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider() -> LLMProvider:
    """Instancia el proveedor LLM configurado en LLM_PROVIDER (.env).

    Cambiar de proveedor es cambiar esa variable de entorno; ningún otro módulo
    (incluido el frontend) necesita modificarse.
    """
    provider_class = _PROVIDERS.get(settings.llm_provider.lower())
    if provider_class is None:
        disponibles = ", ".join(_PROVIDERS.keys())
        raise ValueError(
            f"LLM_PROVIDER='{settings.llm_provider}' no es válido. "
            f"Opciones disponibles: {disponibles}."
        )
    return provider_class()
