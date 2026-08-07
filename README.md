# fisica-chat

Chatbot educativo de Física, pensado para integrarse posteriormente como widget en un
sitio WordPress. Responde utilizando material documental (libros y apuntes en PDF)
proporcionado por el administrador.

**Estado actual: Fase 1** — backend propio + proveedor LLM externo desacoplado +
selección de contexto simple (sin RAG, sin embeddings, sin base vectorial, sin
autenticación, sin persistencia de conversaciones). Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
para el diseño completo y el plan de evolución hacia RAG.

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

## Editar el comportamiento del asistente

Edita `prompts/system_prompt.txt`. Los cambios se aplican en la siguiente consulta, sin
necesidad de tocar código ni reiniciar el servidor.
