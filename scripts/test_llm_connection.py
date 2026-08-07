#!/usr/bin/env python3
"""Prueba de conexión real contra el proveedor LLM configurado en backend/.env.

Uso:
    python scripts/test_llm_connection.py
    python scripts/test_llm_connection.py "¿Qué es la aceleración?"

No guarda nada en disco: solo imprime por stdout. Nunca imprime la API key.
Sale con código 0 si la conexión y la respuesta fueron exitosas, 1 en caso contrario.
"""

import asyncio
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.prompt_loader import load_system_prompt  # noqa: E402
from app.providers.base import LLMProviderError  # noqa: E402
from app.providers.factory import get_provider  # noqa: E402

DEFAULT_QUESTION = "¿Qué es la velocidad y en qué unidades se mide en el Sistema Internacional?"

_MODEL_BY_PROVIDER = {
    "nvidia": settings.nvidia_model,
    "gemini": settings.gemini_model,
    "openrouter": settings.openrouter_model,
}


async def run(question: str) -> int:
    provider_name = settings.llm_provider.lower()
    model = _MODEL_BY_PROVIDER.get(provider_name, "desconocido")

    print(f"Proveedor:  {provider_name}")
    print(f"Modelo:     {model}")
    print(f"Pregunta:   {question}")
    print("-" * 60)

    try:
        provider = get_provider()
        system_prompt = load_system_prompt()
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error de configuración: {exc}")
        return 1

    start = time.perf_counter()
    try:
        answer = await provider.generate(system_prompt, question)
    except LLMProviderError as exc:
        elapsed = time.perf_counter() - start
        print(f"Tiempo hasta el error: {elapsed:.2f}s")
        print(f"Error del proveedor: {exc}")
        return 1
    elapsed = time.perf_counter() - start

    print(f"Tiempo de respuesta: {elapsed:.2f}s")
    print("-" * 60)
    print("Respuesta:")
    print(answer)
    return 0


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION
    exit_code = asyncio.run(run(question))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
