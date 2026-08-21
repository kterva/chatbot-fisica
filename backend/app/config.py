from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> project root is two levels up from backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Proveedor LLM activo: "nvidia", "gemini" u "openrouter"
    llm_provider: str = "nvidia"
    llm_request_timeout_seconds: float = 30.0

    # NVIDIA NIM (API compatible con OpenAI)
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-8b-instruct"

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    # OpenRouter (API compatible con OpenAI)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"

    # Rutas a contenido editable sin tocar código (relativas a la raíz del proyecto)
    prompts_dir: Path = PROJECT_ROOT / "prompts"
    context_dir: Path = PROJECT_ROOT / "context"

    # Seguridad / límites
    allowed_origins: str = "http://localhost:8080"
    max_question_length: int = 500
    rate_limit: str = "10/minute"
    max_context_chars: int = 4000
    # Umbral mínimo de score TF-IDF (ver context_selector.py) para considerar que un
    # archivo de context/ es relevante para la pregunta. Con un corpus grande (varios
    # libros completos, ~100 archivos), casi cualquier pregunta comparte alguna
    # palabra con algún archivo por pura coincidencia estadística — sin este piso,
    # "select_context" casi nunca devuelve vacío y el asistente terminaría
    # respondiendo preguntas totalmente ajenas al material. Calibrado a mano
    # comparando el score de preguntas claramente de Física contra preguntas
    # claramente ajenas (ver docs/TEMARIO.md): hay que volver a calibrarlo si el
    # corpus de context/ cambia mucho de tamaño.
    min_context_score: float = 0.0035

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
