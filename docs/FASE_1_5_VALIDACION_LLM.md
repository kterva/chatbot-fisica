# Fase 1.5 — Validación con proveedor LLM real

## Objetivo

Conectar el backend con un proveedor LLM real (NVIDIA NIM) y validar el comportamiento
educativo del asistente antes de avanzar a una fase RAG. Sin cambios de arquitectura:
solo se ajustó `prompts/system_prompt.txt` a partir de lo observado.

## Configuración utilizada

| Parámetro | Valor |
|---|---|
| Proveedor (`LLM_PROVIDER`) | `nvidia` |
| Modelo (`NVIDIA_MODEL`) | `meta/llama-3.1-8b-instruct` |
| Endpoint | `https://integrate.api.nvidia.com/v1` (API compatible con OpenAI) |
| Selección de contexto | `context/*.txt` de ejemplo (MRU, Leyes de Newton) — ninguna de las preguntas de validación activó contexto relevante, se respondió con conocimiento general del modelo guiado por el system prompt |
| Tiempo de respuesta observado | ~3 a ~20 segundos por consulta |

La API key se cargó desde `backend/.env` (`NVIDIA_API_KEY`), nunca expuesta al
frontend ni impresa en logs. Se verificó primero con `scripts/test_llm_connection.py`
(conexión, modelo y tiempo de respuesta correctos) antes de pasar a las pruebas
pedagógicas.

## Revisión de configuración (sin cambios de código)

Se confirmó, leyendo `backend/app/config.py`, `backend/app/providers/nvidia_nim.py`,
`backend/app/providers/base.py` y `backend/app/main.py`:

- La API key solo se lee de variables de entorno; nunca queda hardcodeada ni se envía
  al navegador.
- `main.py` sigue capturando `LLMProviderError` y devolviendo un 502 genérico al
  cliente, sin exponer detalles internos del proveedor.

No se modificó ningún archivo de código del backend en esta fase.

## Preguntas de validación y hallazgos

### 1. "Explica la diferencia entre velocidad y aceleración usando un ejemplo cotidiano."
**Resultado: correcto.** Explicación clara, con ejemplo del coche en la autopista,
cierra relacionando ambos conceptos con la Segunda Ley de Newton. Buen tono docente.

### 2. "Un automóvil parte del reposo y acelera uniformemente. Explica qué ocurre con su velocidad."
**Resultado: correcto, aunque algo cargado de fórmulas.** Deriva correctamente
`v = v0 + at`, concluye que la velocidad crece linealmente con el tiempo. Ilustra con
un ejemplo numérico propio (no hay error, es un ejemplo genérico, no inventa datos de
un ejercicio del usuario).

### 3. "Explica la segunda ley de Newton para un estudiante de educación media."
**Resultado: correcto.** Buena estructura: definición, ejemplo cualitativo (empujar una
silla), ejemplo numérico, conclusión. Nivel adecuado para Bachillerato.

### 4. "Un estudiante dice que si un cuerpo se mueve necesariamente existe una fuerza aplicada. ¿Cómo responderías?"
**Resultado inicial: problemático.** Con el prompt de la Fase 1 (sin el refuerzo
docente), la respuesta era ambigua: abría con *"si un cuerpo se mueve, existe una
fuerza aplicada en general, pero no necesariamente"* y cerraba calificando la
afirmación del estudiante como *"casi correcta"* — exactamente lo contrario de lo que
se buscaba, porque diluye la corrección de un error conceptual clásico (movimiento sin
fuerza neta, ley de inercia).

## Problema adicional detectado (fuera de las 4 preguntas)

Al probar la conexión con una pregunta simple ("¿Qué es la velocidad...?"), el modelo
respondió inicialmente *"la velocidad es una magnitud escalar"*, lo cual es un error
conceptual (la velocidad es vectorial; la magnitud escalar asociada es la rapidez o
celeridad).

## Ajuste realizado en `prompts/system_prompt.txt`

Se agregaron dos instrucciones puntuales:

1. Al corregir una idea errónea, el asistente debe **abrir la respuesta indicando sin
   ambigüedad si la afirmación es correcta o incorrecta**, y se le prohíbe calificarla
   como "casi correcta" cuando el principio de fondo está mal.
2. Se le pide **prestar especial atención a no confundir magnitudes vectoriales con
   escalares** (velocidad vs. rapidez) y a decir explícitamente cuando no está seguro
   de un dato, en vez de afirmarlo con seguridad.

(También se habían agregado antes, como parte de la preparación de esta fase, las
instrucciones generales pedidas: actuar como profesor y no como solucionario, explicar
el principio antes de la fórmula, evitar respuestas puramente mecánicas, preguntar
cuando falta un dato, y adaptar el lenguaje a educación media.)

## Resultado tras el ajuste

- **Pregunta 4, repetida:** ahora abre con *"Esa idea es incorrecta"* y explica por qué
  con el ejemplo de un objeto en caída libre y en movimiento circular, antes de
  concluir que una fuerza aplicada no es requisito para que un cuerpo se mueva. La
  corrección ya es clara y decisiva, tal como se buscaba.
- **Pregunta de velocidad/unidades, repetida:** ahora responde correctamente *"la
  velocidad es una magnitud vectorial"*.

## Limitación conocida (no resuelta con prompting, pendiente para RAG)

En la respuesta corregida de la pregunta 4, el modelo introdujo una explicación poco
precisa sobre la fuerza centrífuga en movimiento circular (la describe como lo que
"mantiene en movimiento" al objeto, en vez de explicar correctamente el rol de la
fuerza centrípeta y el principio de inercia). Esto no se corrigió con más ajustes de
prompt: es una limitación del modelo base (`llama-3.1-8b-instruct`, un modelo pequeño
de cuota gratuita) al generar ejemplos por su cuenta sin una fuente documental que lo
ancle. Es exactamente el tipo de problema que la futura fase RAG debería mitigar,
forzando al modelo a apoyarse en material curado en vez de generar ejemplos libres.
No se intentó resolver por prompt engineering adicional para evitar iterar
indefinidamente contra una limitación estructural del modelo elegido.

## Conclusión

El flujo completo (widget → `/api/chat` → selección de contexto → system prompt →
NVIDIA NIM → respuesta) funciona de punta a punta con un proveedor real. Tras un
ajuste puntual del prompt, las 4 preguntas de validación obtienen respuestas claras,
de nivel adecuado para Bachillerato, con tono docente y sin errores conceptuales
graves — con la salvedad documentada arriba sobre ejemplos libres no anclados a
material curado, que se resolverá con RAG. No fue necesario ni se realizó ningún
cambio de arquitectura o de código del backend.
