from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

import app.main as main_module
from app.config import settings
from app.main import app
from app.providers.base import LLMProviderError

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["version"]


def test_chat_success(monkeypatch):
    monkeypatch.setattr(main_module.provider, "generate", AsyncMock(return_value="La velocidad es..."))

    response = client.post("/api/chat", json={"question": "¿Qué es la velocidad?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "La velocidad es..."}


def test_chat_rejects_empty_question():
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 422


def test_chat_rejects_oversized_question():
    long_question = "a" * (settings.max_question_length + 1)
    response = client.post("/api/chat", json={"question": long_question})
    assert response.status_code == 422


def test_chat_rejects_question_without_matching_context(monkeypatch):
    # select_context() se mockea directamente en vez de confiar en una pregunta que
    # hoy no matchea ningún archivo de context/: con un corpus grande (varios libros
    # completos) y en crecimiento, cualquier pregunta puede terminar coincidiendo por
    # casualidad con alguna palabra suelta de algún archivo — ver docs/TEMARIO.md,
    # sección de falsos positivos. Lo que este test debe garantizar es el
    # comportamiento del endpoint cuando select_context() no encuentra nada, sin
    # depender del contenido real (y cambiante) de context/.
    monkeypatch.setattr(main_module, "select_context", lambda question: "")
    mock_generate = AsyncMock(return_value="no debería llamarse")
    monkeypatch.setattr(main_module.provider, "generate", mock_generate)

    response = client.post("/api/chat", json={"question": "¿Qué es la aceleración?"})

    assert response.status_code == 200
    assert response.json() == {"answer": main_module.NO_CONTEXT_MESSAGE}
    mock_generate.assert_not_called()


def test_chat_provider_error_hides_internal_detail(monkeypatch):
    async def raise_error(*_args, **_kwargs):
        raise LLMProviderError("detalle interno sensible: API key inválida")

    monkeypatch.setattr(main_module.provider, "generate", raise_error)

    response = client.post("/api/chat", json={"question": "¿Qué es la aceleración?"})

    assert response.status_code == 502
    assert "detalle interno sensible" not in response.text
