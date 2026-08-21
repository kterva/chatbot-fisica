# Temario cubierto por el material de contexto

Este documento lista los temas sobre los que el asistente tiene material documental
propio en `context/` (ver `app/context_selector.py`). Para preguntas fuera de este
temario, el asistente **no responde**: si `select_context()` no encuentra ningún
archivo relacionado con la pregunta, `main.py` devuelve un mensaje fijo sin llamar al
proveedor LLM (ver `NO_CONTEXT_MESSAGE` en `app/main.py`). El system prompt además
instruye al modelo a no completar con conocimiento propio ni siquiera cuando el
contexto encontrado es parcial.

> **Limitación conocida**: la selección de contexto es naive (coincidencia de
> palabras clave, ver `ARCHITECTURE.md`). Una pregunta genuinamente cubierta por el
> material, pero formulada con vocabulario distinto al de los archivos de `context/`,
> puede no encontrar coincidencias y rechazarse igual — falso negativo, no falso
> positivo. Se prefirió este trade-off explícitamente: es preferible que rechace una
> pregunta que sí podría responder, a que responda algo sin respaldo documental.

Actualizar esta lista cada vez que se agregue un documento nuevo (ver
[README.md](../README.md#agregar-material-documental)).

## Archivos de ejemplo (contenido acotado)

- **`cinematica_mru.txt`** — Movimiento Rectilíneo Uniforme (MRU): definición, ecuación
  fundamental, velocidad constante.
- **`leyes_de_newton.txt`** — Primera, Segunda y Tercera Ley de Newton.

## Libro "La Física entre nosotros 5" (Bachillerato)

Extraído por OCR y **separado en un archivo por capítulo** (`libro5_capN_*.txt`) —
el libro completo en un solo archivo hacía que la selección de contexto (naive, ver
`ARCHITECTURE.md`) devolviera siempre la tabla de contenidos en vez del capítulo
relevante, por el límite `MAX_CONTEXT_CHARS`. Separado por capítulo, cada archivo
sigue siendo grande (25-70K caracteres) comparado con `MAX_CONTEXT_CHARS` (4000), así
que dentro de un capítulo largo puede seguir devolviendo el inicio del capítulo y no
la sección exacta — mejora real, no solución completa (eso es trabajo de RAG).

1. **`libro5_cap1_cinematica.txt`** — movimientos rectilíneos, posición,
   desplazamiento, velocidad media e instantánea, M.R.U., aceleración, M.R.U.V.,
   caída libre.
2. **`libro5_cap2_movimiento_2d.txt`** — posición, desplazamiento, rapidez y
   velocidad media/instantánea, aceleración media, composición de M.R.U.,
   movimiento de proyectiles.
3. **`libro5_cap3_dinamica.txt`** — fuerza, masa puntual, peso, normal,
   rozamiento/fricción, fuerza elástica, fuerza neta, las tres Leyes de Newton,
   masas vinculadas, estática, condición de equilibrio, Ley de Gravitación
   Universal.
4. **`libro5_cap4_trabajo_energia.txt`** — trabajo de una fuerza (constante y
   variable), energía cinética, fuerzas conservativas y energía potencial
   (gravitatoria y elástica), fuerzas no conservativas, conservación de la
   energía mecánica.
5. **`libro5_cap5_cantidad_movimiento.txt`** — impulso de una fuerza (constante y
   variable), cantidad de movimiento, principio de conservación, choques y
   energía, centro de masa.
6. **`libro5_cap6_movimiento_circular.txt`** — medidas angulares, M.C.U. (período,
   frecuencia, velocidad angular y tangencial), aceleración y fuerza centrípeta,
   M.C.U.V., carácter vectorial de las magnitudes rotacionales.
7. **`libro5_cap7_dinamica_rotacional.txt`** — cuerpo rígido, torque o momento de
   una fuerza, torque neto y equilibrio de rotación, momento de inercia, energía
   cinética rotacional, momento cinético.
8. **`libro5_cap8_termodinamica.txt`** — termodinámica (leyes de los gases
   ideales, procesos termodinámicos, primer principio).
9. **`libro5_cap9_fluidos.txt`** — presión en un fluido, Ley de Pascal, Principio
   de Arquímedes, dinámica de fluidos (ecuación de continuidad, Bernoulli).

Cada capítulo incluye además problemas resueltos y problemas de examen, que el
asistente puede usar como ejemplos. **No se incluyó** la sección final de
"Soluciones" (respuestas numéricas sueltas, sin el enunciado del problema): mezclada
sin contexto, podría empujar al asistente a dar la respuesta final directa en vez de
razonar el problema, contra lo que pide `prompts/system_prompt.txt`.

> **Nota de calidad**: el texto viene de OCR y tiene ruido reconocible (acentos
> perdidos, dígitos/letras confundidos como "10OKg", palabras con guion de corte mal
> resuelto, algún typo tipo "desapreciable" en vez de "despreciable"). No se corrigió
> a mano todavía. Es usable como fuente, pero si el asistente da una respuesta rara en
> un tema de este libro, conviene revisar el `.txt` antes de asumir que es un error del
> modelo.
