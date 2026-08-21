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
    "quién", "quien", "quiénes", "quienes", "cuándo", "cuando", "dónde", "donde",
    "cuánta", "cuanta", "cuántas", "cuantas", "cuántos", "cuantos",
}

_WORD_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")

# Siglas como "M.R.U.V." (Movimiento Rectilíneo Uniformemente Variado) o "M.C.U."
# (Movimiento Circular Uniforme) son vocabulario central de estos libros, escritas
# casi siempre con un punto entre cada letra. Sin esta normalización, _WORD_RE las
# parte en letras sueltas de largo 1 que el filtro de longitud descarta, y la sigla
# "MRU"/"MRUV" (como la escribiría un estudiante, sin puntos) casi no tiene señal en
# el corpus aunque el tema esté ampliamente cubierto.
_DOTTED_ACRONYM_RE = re.compile(r"\b(?:[a-zA-Z]\.){2,}")

# Fragmentos más cortos que esto (títulos sueltos, restos de OCR) se fusionan con el
# siguiente en vez de puntuarse como unidad propia: son demasiado chicos para que su
# conteo de palabras signifique algo.
MIN_CHUNK_CHARS = 200

# Fragmentos con menos palabras "de contenido" (post-tokenización) que esto se
# descartan directamente de la selección, aunque superen MIN_CHUNK_CHARS: suelen ser
# tablas de respuestas o listas de ejercicios resueltos con muchos números/símbolos y
# poco texto real, donde una sigla repetida unas pocas veces (ej. "M.R.U." en una
# tabla de soluciones) dispara el score de forma artificial por la poca cantidad de
# palabras totales — no son un buen contexto explicativo para el modelo de todas
# formas. Encontrado en la práctica: una tabla de respuestas en un capítulo de
# fluidos, con solo 33 palabras, superaba en score a los párrafos explicativos reales
# del capítulo de cinemática para la pregunta "MRU".
MIN_CHUNK_WORDS = 40


def _raw_words(text: str) -> list[str]:
    text = _DOTTED_ACRONYM_RE.sub(lambda m: m.group(0).replace(".", ""), text)
    return _WORD_RE.findall(text.lower())


def _tokenize(text: str) -> list[str]:
    words = _raw_words(text)
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _tokenize_with_bigrams(text: str) -> list[str]:
    """Como `_tokenize`, pero además agrega bigramas (pares de palabras adyacentes,
    ej. "espacio_recorrido") a la lista.

    Puntuar solo palabras sueltas no distingue "Movimiento Rectilíneo Uniformemente
    Variado" de "Movimiento Circular Uniformemente Variado": comparten casi todas
    las palabras clave, y un fragmento que repite mucho una sola de ellas (ej.
    "recorrido") le puede ganar en score al fragmento realmente relevante aunque no
    tenga nada que ver con el tema. Los bigramas capturan la frase compuesta como
    unidad — "movimiento_rectilíneo" o "rectilíneo_uniformemente" solo matchean
    fragmentos que genuinamente usan esa combinación, no cualquiera que use alguna
    de las palabras sueltas por separado. Encontrado en la práctica con exactamente
    ese caso (MRUV vs. movimiento circular).
    """
    words = _raw_words(text)
    unigrams = [w for w in words if w not in STOPWORDS and len(w) > 2]
    bigrams = []
    for first, second in zip(words, words[1:]):
        if (
            first not in STOPWORDS
            and len(first) > 2
            and second not in STOPWORDS
            and len(second) > 2
        ):
            bigrams.append(f"{first}_{second}")
    return unigrams + bigrams


def _split_into_chunks(text: str) -> list[str]:
    """Parte el texto de un archivo en fragmentos delimitados por líneas en blanco
    (párrafos o secciones, según cómo haya quedado el texto extraído del PDF).

    Los capítulos completos de los libros cargados en context/ tienen decenas de
    miles de caracteres (mediana ~110.000, hasta ~340.000) — puntuar el archivo
    entero como una sola unidad, como se hacía antes, tenía dos problemas: (1) un
    capítulo ajeno pero con vocabulario parecido (ej. "Movimiento Circular
    Uniformemente Variado" vs "Movimiento Rectilíneo Uniformemente Variado") podía
    ganarle por muy poco al capítulo correcto, y (2) aun ganando el capítulo
    correcto, solo se enviaban al modelo sus primeros MAX_CONTEXT_CHARS caracteres
    (el arranque/introducción), nunca el desarrollo ni los ejemplos que suelen estar
    más adelante. Partiendo en fragmentos y puntuando cada uno por separado, una
    pregunta puede encontrar el fragmento específico que la responde esté donde esté
    dentro del capítulo, y ya no compite un capítulo entero contra otro.
    """
    raw_parts = [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for part in raw_parts:
        buffer = f"{buffer}\n\n{part}" if buffer else part
        if len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        if chunks:
            chunks[-1] = f"{chunks[-1]}\n\n{buffer}"
        else:
            chunks.append(buffer)
    return chunks


def select_context(question: str) -> str:
    """Selección de contexto naive: puntúa cada fragmento (párrafo/sección) de cada
    archivo .txt de context/ con TF-IDF simplificado (sin embeddings) sobre las
    palabras clave de la pregunta, y concatena los fragmentos más relevantes de todo
    el corpus hasta un presupuesto máximo de caracteres.

    TF (frecuencia del término): cuántas veces aparece la palabra (o bigrama, ver
    `_tokenize_with_bigrams`) en el fragmento, normalizado por el largo del
    fragmento. IDF (frecuencia inversa de documento, acá "documento" = fragmento, no
    archivo): fragmentos que comparten una palabra con casi cualquier otro fragmento
    del corpus (ej. "fuerza", "newton" — comunes en cualquier texto de Física) no
    discriminan nada y se les baja el peso casi a cero; palabras específicas de
    pocos fragmentos (ej. "refracción") pesan mucho más.

    Este es el único punto que deberá cambiar al migrar a búsqueda semántica /
    embeddings en una fase RAG posterior; su firma (question -> str) no cambiará.
    """
    if not settings.context_dir.is_dir():
        return ""

    question_words = set(_tokenize_with_bigrams(question))
    if not question_words:
        return ""

    paths = sorted(settings.context_dir.glob("*.txt"))
    if not paths:
        return ""

    # Se lee y trocea cada archivo una sola vez, y se tokeniza cada fragmento: hace
    # falta más de una pasada (document frequency, después scoring), así que se
    # guarda todo en memoria durante el request en vez de releer/retrocear del disco.
    chunk_data = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for chunk in _split_into_chunks(text):
            counts = Counter(_tokenize_with_bigrams(chunk))
            # El denominador de TF se calcula solo sobre unigramas (no cuenta los
            # bigramas agregados) para que la escala de los scores, y por lo tanto
            # MIN_CONTEXT_SCORE, no cambie por este agregado.
            total_words = sum(v for k, v in counts.items() if "_" not in k)
            if total_words < MIN_CHUNK_WORDS:
                continue
            chunk_data.append((path, chunk, counts, total_words))

    doc_freq: Counter[str] = Counter()
    for _path, _chunk, counts, _total in chunk_data:
        for word in question_words:
            if word in counts:
                doc_freq[word] += 1

    n_chunks = len(chunk_data)
    scored_chunks = []
    for path, chunk, counts, total_words in chunk_data:
        score = 0.0
        for word in question_words:
            count = counts.get(word)
            if not count:
                continue
            tf = count / total_words
            idf = math.log(n_chunks / doc_freq[word])
            score += tf * idf
        if score >= settings.min_context_score:
            scored_chunks.append((score, path, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    selected_chunks = []
    remaining_budget = settings.max_context_chars
    for _score, path, chunk in scored_chunks:
        if remaining_budget <= 0:
            break
        piece = chunk[:remaining_budget]
        selected_chunks.append(f"[Fuente: {path.name}]\n{piece}")
        remaining_budget -= len(piece)

    return "\n\n".join(selected_chunks)
