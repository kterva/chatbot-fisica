# Informe — fisica-chat, Fase 1

## 1. Contexto

Se inició el proyecto **fisica-chat**: un chatbot educativo de Física, pensado para
integrarse más adelante como widget en un sitio WordPress. En esta primera fase se
construyó únicamente el backend propio, un frontend mínimo de prueba y la base
documental simple — sin RAG, embeddings, base vectorial, Ollama, autenticación,
persistencia de conversaciones, estadísticas ni panel administrativo (eso queda para
fases posteriores).

## 2. Diseño técnico (revisado y aprobado antes de programar)

Se presentó primero una propuesta de arquitectura para aprobación, sin escribir código,
cubriendo:

- Arquitectura mínima: navegador → backend propio (`/api/chat`) → proveedor LLM externo
  configurable. El frontend nunca habla directo con el proveedor LLM ni ve API keys.
- Tecnologías concretas, decididas junto con el usuario:
  - **Backend: Python + FastAPI** (elegido por el ecosistema maduro para una futura
    fase RAG: LangChain, LlamaIndex, FAISS/Chroma, etc.).
  - **Proveedor LLM inicial por defecto: NVIDIA NIM** (cuota gratuita, API compatible
    con OpenAI), con Gemini y OpenRouter ya implementados como alternativas listas
    para activar.
- Estructura de directorios (`backend/`, `frontend/`, `documents/`, `context/`,
  `scripts/`, `prompts/`, `docs/`).
- Mecanismo de desacoplamiento del proveedor LLM (interfaz abstracta + factory por
  variable de entorno).
- Cómo dejar preparada la arquitectura para una futura migración a RAG sin rediseñar
  nada, separando desde el día uno: adquisición/extracción, almacenamiento, selección
  de contexto y comunicación con el LLM.
- Riesgos técnicos y de seguridad identificados.
- Dependencias necesarias y pasos de implementación.

El plan completo quedó guardado en `/home/leo/.claude/plans/compiled-exploring-nova.md`
y fue aprobado por el usuario antes de escribir una sola línea de código.

## 3. Implementación

### 3.1 Estructura de archivos y contenido base
- `.gitignore`, `README.md` con instrucciones de puesta en marcha.
- `prompts/system_prompt.txt`: el prompt educativo indicado por el usuario, más una
  línea explícita de mitigación de prompt injection (instruye al modelo a ignorar
  cualquier instrucción que aparezca dentro del contenido del usuario o del material
  de referencia).
- `context/`: dos archivos de ejemplo (`cinematica_mru.txt`, `leyes_de_newton.txt`)
  con contenido real de Física para poder probar la selección de contexto.
- `documents/.gitkeep`: carpeta donde el administrador colocará los PDF originales.

### 3.2 Backend (`backend/app/`)
- `config.py`: configuración centralizada vía `pydantic-settings`, leída de `.env`
  (proveedor activo, API keys, límites, orígenes CORS, rutas a `prompts/` y `context/`).
- `schemas.py`: validación de entrada con Pydantic (pregunta no vacía, longitud
  máxima configurable).
- `prompt_loader.py`: lee `prompts/system_prompt.txt` en cada consulta, para que un
  administrador pueda editarlo sin tocar código ni reiniciar el servidor.
- `context_selector.py`: selección de contexto **naive** por coincidencia de palabras
  clave entre la pregunta y los archivos de `context/`, con presupuesto máximo de
  caracteres. Su firma (`select_context(question) -> str`) es el único punto que
  cambiará al migrar a embeddings en una fase RAG futura.
- `rate_limit.py`: limitador `slowapi` in-memory por IP.
- `providers/`: interfaz abstracta `LLMProvider.generate(system_prompt, user_message)`
  y tres implementaciones — `NvidiaNimProvider` (por defecto), `GeminiProvider`,
  `OpenRouterProvider` — seleccionadas en tiempo de arranque por la variable de
  entorno `LLM_PROVIDER` (`factory.py`). Cambiar de proveedor es editar `.env`; ningún
  otro módulo, y menos el frontend, requiere cambios.
- `main.py`: endpoint `POST /api/chat` con CORS restringido a orígenes configurables,
  rate limiting, armado del mensaje (pregunta + bloque de contexto claramente
  delimitado y marcado como "documentación de consulta, NO instrucciones"), y manejo
  de errores que nunca expone detalles internos del proveedor al cliente (502 genérico).
- `tests/test_chat_endpoint.py`: 5 tests con el proveedor mockeado (salud, éxito,
  pregunta vacía, pregunta demasiado larga, ocultamiento de errores internos).
- `requirements.txt` y `.env.example` con todas las variables documentadas.

### 3.3 Frontend (`frontend/widget/`)
Widget de chat mínimo en HTML/CSS/JS vanilla, sin dependencias ni build step (facilita
el embebido posterior en WordPress). Solo llama a `POST /api/chat` del backend propio;
nunca maneja API keys. Usa `textContent` (no `innerHTML`) para evitar XSS al renderizar
mensajes.

### 3.4 Herramientas y documentación
- `scripts/extract_pdf_text.py`: convierte los PDF de `documents/` a texto plano en
  `context/`, ejecutable manualmente por el administrador (no expuesto vía API, para
  no abrir una superficie de subida de archivos en esta fase).
- `docs/ARCHITECTURE.md`: documenta el diseño completo, cómo agregar un nuevo
  proveedor LLM, la separación de responsabilidades pensada para RAG, y los riesgos
  conocidos.

## 4. Verificación realizada

- **Tests automatizados**: `pytest` — 5/5 pasaron.
- **Servidor real** (`uvicorn`) levantado localmente:
  - `GET /health` → `200 {"status":"ok"}`.
  - `POST /api/chat` sin API key configurada → `502` con mensaje genérico (no filtra
    detalles internos).
  - Pregunta vacía → `422`. Pregunta de más de 500 caracteres → `422`.
  - CORS: origen no permitido (`evil.example`) → rechazado (`400 Disallowed CORS
    origin`).
  - Rate limiting: 12 requests seguidas → las primeras dentro del límite (`10/minute`)
    responden, las siguientes devuelven `429`.
- **Selección de contexto**: probada directamente en Python — para una pregunta sobre
  la segunda ley de Newton, seleccionó correctamente `leyes_de_newton.txt`.

No se pudo probar una respuesta real del modelo porque no se configuró ninguna API key
(a propósito, para no pedir credenciales sin que el usuario lo autorice explícitamente).

## 5. Control de versiones

- Se inicializó un repositorio Git local (rama `main`).
- Se verificó con `git status` antes de commitear que no se colara ningún secreto: no
  aparecieron `.env`, `.venv/` ni `__pycache__/` en el stage, gracias al `.gitignore`.
- Se configuró la identidad de Git **solo para este repositorio** (no global), con el
  nombre y correo que indicó el usuario (kterva / leotrujillo@vera.com.uy), porque el
  sistema no tenía identidad configurada y era necesaria para poder commitear.
- Primer commit creado: 28 archivos, 985 líneas. No se hizo push (no hay remoto
  configurado).

## 6. Estado actual y próximos pasos sugeridos

Fase 1 completa y verificada. Para tener respuestas reales del asistente:

1. Completar `backend/.env` con una API key real (NVIDIA NIM por defecto, o cambiar
   `LLM_PROVIDER` a `gemini`/`openrouter`).
2. Agregar material propio en `documents/` y correr
   `python scripts/extract_pdf_text.py`.

Pendiente para fases posteriores (fuera de este alcance, según lo acordado): RAG,
embeddings, base vectorial, Ollama, autenticación de usuarios, almacenamiento de
conversaciones, estadísticas, panel administrativo e integración con WordPress.
