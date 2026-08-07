# Arquitectura — fisica-chat (Fase 1)

## Objetivo de esta fase

Backend propio que media entre un futuro widget de WordPress y un proveedor LLM externo
configurable, usando un conjunto simple de documentos de Física como referencia. Sin
RAG/embeddings/base vectorial, sin autenticación de usuarios, sin persistencia de
conversaciones. Esas capacidades se agregan en fases posteriores sobre la misma base.

## Flujo de una consulta

```
Navegador (widget)
   │  POST /api/chat { question }
   ▼
FastAPI /api/chat
   ├─ Pydantic valida question (longitud, no vacío)
   ├─ slowapi aplica rate limiting por IP
   ├─ prompt_loader.load_system_prompt()   ← prompts/system_prompt.txt
   ├─ context_selector.select_context(question)  ← context/*.txt
   ├─ arma mensaje de usuario = pregunta + bloque de contexto delimitado
   ├─ provider.generate(system_prompt, user_message)  ← LLMProvider activo
   └─ responde { answer } (o 429/422/502 con mensaje genérico)
```

El frontend solo conoce la URL del backend. Nunca ve una API key de proveedor LLM.

## Proveedor LLM desacoplado

`app/providers/base.py` define la interfaz `LLMProvider.generate(system_prompt, user_message) -> str`.
`app/providers/factory.py` instancia la implementación indicada por `LLM_PROVIDER` (env var):

| LLM_PROVIDER | Implementación | Formato de API |
|---|---|---|
| `nvidia` (por defecto) | `NvidiaNimProvider` | Compatible con OpenAI (chat completions) |
| `openrouter` | `OpenRouterProvider` | Compatible con OpenAI (chat completions) |
| `gemini` | `GeminiProvider` | API propia de Google (`generateContent`) |

`NvidiaNimProvider` y `OpenRouterProvider` heredan de `OpenAICompatibleProvider` (en
`base.py`), que implementa una sola vez la llamada HTTP a un endpoint `/chat/completions`
estilo OpenAI. `GeminiProvider` implementa la llamada por separado porque el formato de
la API de Gemini es distinto.

`main.py` solo importa `LLMProvider` y llama a `.generate(...)`; nunca conoce detalles
de una API concreta. **Cambiar de proveedor = cambiar `LLM_PROVIDER` (y su API key) en
`.env` y reiniciar el proceso.** No requiere tocar frontend ni el resto del backend.

### Agregar un nuevo proveedor LLM

1. Crear `app/providers/<nombre>.py` con una clase que implemente `LLMProvider.generate`
   (o que herede de `OpenAICompatibleProvider` si la API es compatible con OpenAI).
2. Agregar sus variables de configuración a `app/config.py` y a `.env.example`.
3. Registrar la clase en el diccionario `_PROVIDERS` de `app/providers/factory.py`.
4. Ningún otro archivo necesita cambios.

Esto también es el camino para integrar Ollama en el futuro (self-hosted): sería un
proveedor más con `generate()` apuntando a `http://localhost:11434/api/chat`.

## Separación de responsabilidades documentales (preparación para RAG)

Se mantienen ya separadas 4 responsabilidades independientes, cada una con una interfaz
mínima, para que una futura migración a RAG sea un cambio localizado:

1. **Adquisición/extracción** — `scripts/extract_pdf_text.py`: `documents/*.pdf` → `context/*.txt`.
   Se ejecuta manualmente por el administrador (no expuesto vía API, evita superficie de
   ataque de subida de archivos). En el futuro podría producir chunks con metadatos en
   vez de un `.txt` por documento.
2. **Almacenamiento** — `context/`: hoy archivos de texto plano. En el futuro, una base
   vectorial (Chroma, FAISS, pgvector, etc.).
3. **Selección de contexto** — `app/context_selector.py`, función
   `select_context(question: str) -> str`. Hoy: coincidencia simple de palabras clave
   (naive keyword matching) entre la pregunta y cada archivo de `context/`, con un
   presupuesto máximo de caracteres (`MAX_CONTEXT_CHARS`). En el futuro: embeddings +
   búsqueda por similitud semántica. **La firma de la función no cambia**, por lo que
   `main.py` no requiere modificaciones al migrar.
4. **Comunicación con el LLM** — `app/providers/`: ya desacoplada de la selección de
   contexto y de la extracción documental; no requiere cambios para RAG.

## Seguridad

- **Secretos**: solo por variables de entorno (`backend/.env`, no versionado). Se
  provee `backend/.env.example` con placeholders. `.env` está en `.gitignore`.
- **Validación de entrada**: `app/schemas.py` limita la longitud de `question`
  (`MAX_QUESTION_LENGTH`, por defecto 500 caracteres) y rechaza preguntas vacías.
- **Rate limiting**: `slowapi`, in-memory, por IP (`RATE_LIMIT`, por defecto
  `10/minute`). *Limitación conocida*: no persiste entre reinicios ni se comparte entre
  múltiples workers/instancias; sería necesario un backend compartido (p. ej. Redis) si
  se escala horizontalmente.
- **CORS**: restringido a los orígenes listados en `ALLOWED_ORIGINS`, nunca `*`.
- **Prompt injection**: el contenido de `context/` y la pregunta del usuario se envían
  siempre en el rol `user`, dentro de un bloque delimitado y explícitamente marcado como
  "documentación de consulta, NO instrucciones". El propio `prompts/system_prompt.txt`
  instruye al modelo a ignorar cualquier instrucción que aparezca dentro de ese
  contenido. No es una garantía absoluta frente a un modelo adversarialmente manipulado,
  pero es la mitigación estándar razonable para esta fase.
- **Errores**: `LLMProviderError` se captura en `main.py` y se traduce a un mensaje
  genérico (HTTP 502); nunca se reenvía el detalle interno (que puede incluir fragmentos
  de URLs o de la respuesta cruda del proveedor) al cliente.
- **Timeouts**: toda llamada HTTP a un proveedor usa `LLM_REQUEST_TIMEOUT_SECONDS`.

## Riesgos conocidos y pendientes para fases posteriores

- Sin autenticación de usuarios: cualquiera con la URL pública del backend puede
  consumir la cuota del proveedor configurado. Mitigado parcialmente por CORS + rate
  limiting; deberá revisarse antes de una exposición pública amplia (posible fase con
  autenticación o proxy desde WordPress).
- Rate limiting in-memory no escala a múltiples instancias del backend.
- Selección de contexto naive puede no encontrar el fragmento más relevante, o
  seleccionar contenido parcialmente relevante; se resolverá con embeddings en la fase RAG.
- Dependencia de la cuota gratuita de un único proveedor a la vez; el desacoplamiento
  permite cambiar rápido, pero no hay failover automático en esta fase.
