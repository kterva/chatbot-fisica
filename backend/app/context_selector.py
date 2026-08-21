import math
import re
from collections import Counter

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


def _tokenize(text: str) -> list[str]:
    words = _WORD_RE.findall(text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def select_context(question: str) -> str:
    """Selección de contexto naive: puntúa cada archivo .txt de context/ con
    TF-IDF simplificado (sin embeddings) sobre las palabras clave de la pregunta, y
    concatena los más relevantes hasta un presupuesto máximo de caracteres.

    TF (frecuencia del término): cuántas veces aparece la palabra en el archivo,
    normalizado por el largo del archivo — un archivo chico y enfocado en el tema le
    da más peso relativo a esa palabra que un capítulo entero donde aparece de
    pasada. IDF (frecuencia inversa de documento): palabras que aparecen en casi
    todos los archivos del corpus (ej. "fuerza", "newton" — comunes en cualquier
    texto de Física) no discriminan nada y se les baja el peso casi a cero; palabras
    específicas (ej. "refracción") pesan mucho más. Con el corpus original (2-3
    archivos chicos y temáticos) contar coincidencias simples alcanzaba; con ~100
    archivos (varios libros completos por capítulo) dejó de alcanzar — dos archivos
    empataban en coincidencias simples aunque solo uno fuera relevante, y el empate
    se resolvía alfabéticamente en vez de por relevancia.

    Este es el único punto que deberá cambiar al migrar a búsqueda semántica /
    embeddings en una fase RAG posterior; su firma (question -> str) no cambiará.
    """
    if not settings.context_dir.is_dir():
        return ""

    question_words = set(_tokenize(question))
    if not question_words:
        return ""

    paths = sorted(settings.context_dir.glob("*.txt"))
    if not paths:
        return ""

    # Se lee y tokeniza cada archivo una sola vez y se guarda en memoria: hace falta
    # más de una pasada (document frequency, después scoring), pero releer/retokenizar
    # del disco sería más caro que guardar los conteos de ~100 archivos en RAM durante
    # el request.
    file_data = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        counts = Counter(_tokenize(text))
        total_words = sum(counts.values())
        file_data.append((path, text, counts, total_words))

    doc_freq: Counter[str] = Counter()
    for _path, _text, counts, _total in file_data:
        for word in question_words:
            if word in counts:
                doc_freq[word] += 1

    n_files = len(paths)
    scored_files = []
    for path, text, counts, total_words in file_data:
        if total_words == 0:
            continue
        score = 0.0
        for word in question_words:
            count = counts.get(word)
            if not count:
                continue
            tf = count / total_words
            idf = math.log(n_files / doc_freq[word])
            score += tf * idf
        if score >= settings.min_context_score:
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
