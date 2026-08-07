import re

from app.config import settings

# Palabras muy frecuentes en español que aportan poco a la coincidencia por palabras
# clave. Lista deliberadamente corta: la selección de contexto es intencionalmente
# simple en esta fase (ver docs/ARCHITECTURE.md).
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "en", "y", "o",
    "que", "qué", "es", "son", "para", "por", "con", "sin", "se", "su", "sus", "al",
    "cómo", "como", "cuál", "cual", "cuáles", "cuales", "cuánto", "cuanto", "porque",
    "más", "mas", "muy", "si", "no", "lo", "le", "les", "a", "e", "hay",
}

_WORD_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+")


def _tokenize(text: str) -> set[str]:
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def select_context(question: str) -> str:
    """Selección de contexto naive: puntúa cada archivo .txt de context/ por la
    cantidad de palabras clave que comparte con la pregunta, y concatena los más
    relevantes hasta un presupuesto máximo de caracteres.

    Este es el único punto que deberá cambiar al migrar a búsqueda semántica /
    embeddings en una fase RAG posterior; su firma (question -> str) no cambiará.
    """
    if not settings.context_dir.is_dir():
        return ""

    question_words = _tokenize(question)
    if not question_words:
        return ""

    scored_files = []
    for path in sorted(settings.context_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        file_words = _tokenize(text)
        score = len(question_words & file_words)
        if score > 0:
            scored_files.append((score, path, text))

    scored_files.sort(key=lambda item: item[0], reverse=True)

    selected_chunks = []
    remaining_budget = settings.max_context_chars
    for _score, path, text in scored_files:
        if remaining_budget <= 0:
            break
        chunk = text.strip()[:remaining_budget]
        selected_chunks.append(f"[Fuente: {path.name}]\n{chunk}")
        remaining_budget -= len(chunk)

    return "\n\n".join(selected_chunks)
