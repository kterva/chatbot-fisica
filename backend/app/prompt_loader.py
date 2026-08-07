from app.config import settings


def load_system_prompt() -> str:
    """Lee el prompt del sistema desde prompts/system_prompt.txt en cada llamada,
    para que un administrador pueda editarlo sin reiniciar el servidor."""
    prompt_path = settings.prompts_dir / "system_prompt.txt"
    if not prompt_path.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo de prompt del sistema: {prompt_path}"
        )
    return prompt_path.read_text(encoding="utf-8").strip()
