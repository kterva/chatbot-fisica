import httpx

from app.config import settings
from app.providers.base import LLMProvider, LLMProviderError


class GeminiProvider(LLMProvider):
    """Google Gemini usa un formato de API distinto al de OpenAI (generateContent)."""

    def __init__(self):
        self._base_url = settings.gemini_base_url.rstrip("/")
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model

    async def generate(self, system_prompt: str, user_message: str) -> str:
        if not self._api_key:
            raise LLMProviderError("Falta configurar la API key de Gemini.")

        url = f"{self._base_url}/models/{self._model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
        }
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Error de comunicación con Gemini: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"Respuesta inesperada de Gemini: {exc}") from exc
