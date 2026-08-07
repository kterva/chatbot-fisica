from abc import ABC, abstractmethod

import httpx

from app.config import settings


class LLMProviderError(Exception):
    """Error genérico al comunicarse con el proveedor LLM.

    Los mensajes de esta excepción son seguros para mostrar en logs internos, pero
    quien la captura en main.py debe devolver al cliente un mensaje genérico, nunca
    este mensaje ni la excepción original (puede contener detalles de la API).
    """


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> str:
        """Envía system_prompt + user_message al proveedor y devuelve la respuesta.

        Implementaciones deben capturar errores de red/HTTP/parseo y relanzarlos como
        LLMProviderError.
        """
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """Implementación reutilizable para proveedores con API estilo OpenAI
    (chat completions): NVIDIA NIM y OpenRouter la usan tal cual, cambiando solo
    base_url, api_key y model."""

    def __init__(self, base_url: str, api_key: str, model: str, provider_name: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._provider_name = provider_name

    async def generate(self, system_prompt: str, user_message: str) -> str:
        if not self._api_key:
            raise LLMProviderError(f"Falta configurar la API key de {self._provider_name}.")

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Error de comunicación con {self._provider_name}: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(
                f"Respuesta inesperada de {self._provider_name}: {exc}"
            ) from exc
