# fisica-chat

Chatbot educativo de Física, pensado para integrarse posteriormente como widget en un
sitio WordPress. Responde utilizando material documental (libros y apuntes en PDF)
proporcionado por el administrador.

**Estado actual: Fase 1.5** — backend propio + proveedor LLM externo desacoplado +
selección de contexto simple, ya validado contra NVIDIA NIM real (sin RAG, sin
embeddings, sin base vectorial, sin autenticación, sin persistencia de conversaciones).
Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para el diseño completo y
[docs/FASE_1_5_VALIDACION_LLM.md](docs/FASE_1_5_VALIDACION_LLM.md) para la validación
pedagógica realizada.

## Estructura

```
fisica-chat/
├── backend/     # API FastAPI (/api/chat)
├── frontend/    # Widget de chat mínimo (HTML/CSS/JS vanilla)
├── documents/   # PDFs/apuntes originales aportados por el administrador
├── context/     # Texto plano extraído de documents/, consumido por el backend
├── scripts/     # Herramientas de extracción (PDF -> texto)
├── prompts/     # Instrucciones del asistente (editable sin tocar código)
└── docs/        # Documentación técnica
```

## Puesta en marcha rápida (desarrollo local)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completa tu API key del proveedor elegido
uvicorn app.main:app --reload
```

En otra terminal, sirve el widget de prueba:

```bash
cd frontend/widget
python3 -m http.server 8080
```

Abre `http://localhost:8080/chat-widget.html` en el navegador.

## Probar con un proveedor real (NVIDIA NIM)

La Fase 1 corre con cualquier `LLM_PROVIDER` sin API key configurada (los errores del
proveedor se ocultan al usuario), pero para tener respuestas reales del asistente:

1. Consigue una API key gratuita en [build.nvidia.com](https://build.nvidia.com) (creá
   una cuenta y generá una API key desde cualquier modelo del catálogo).
2. Pégala en `backend/.env` (creado a partir de `.env.example`), en la variable
   `NVIDIA_API_KEY`. Ese archivo está en `.gitignore`: nunca se sube al repositorio.
3. Corre una prueba de conexión rápida, sin depender del servidor ni del frontend:
   ```bash
   cd backend && source .venv/bin/activate
   python ../scripts/test_llm_connection.py
   ```
   Debería imprimir el proveedor, el modelo, el tiempo de respuesta y una respuesta real.
   Si el modelo configurado (`NVIDIA_MODEL`) no está disponible, probá otro del catálogo
   de build.nvidia.com y actualizá esa variable en `.env`.
4. Para probar una conversación completa, levantá el backend (`uvicorn app.main:app --reload`)
   y hacé una consulta real:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"question":"¿Qué es la segunda ley de Newton?"}'
   ```
   o abrí el widget (`frontend/widget/chat-widget.html`, servido como se indica arriba)
   y conversá desde el navegador.

## Cambiar de proveedor LLM

Edita `backend/.env`: cambia `LLM_PROVIDER` (`nvidia`, `gemini` u `openrouter`) y la API
key correspondiente. No requiere cambios en el frontend ni en el resto del backend.
Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#agregar-un-nuevo-proveedor-llm) para
agregar un proveedor nuevo.

## Agregar material documental

1. Coloca los PDF en `documents/`.
2. Ejecuta `python scripts/extract_pdf_text.py` para generar los `.txt` correspondientes
   en `context/`.
3. El backend los usa automáticamente en la siguiente consulta (no requiere reinicio).
4. Actualiza [docs/TEMARIO.md](docs/TEMARIO.md) con los temas que cubre el documento
   nuevo, para llevar registro de qué puede responder el asistente con material propio.

## Editar el comportamiento del asistente

Edita `prompts/system_prompt.txt`. Los cambios se aplican en la siguiente consulta, sin
necesidad de tocar código ni reiniciar el servidor.
