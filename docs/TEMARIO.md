# Temario cubierto por el material de contexto

Este documento lista los temas sobre los que el asistente tiene material documental
propio en `context/` (ver `app/context_selector.py`). Para preguntas fuera de este
temario, el asistente **no responde**: si `select_context()` no encuentra ningún
archivo relacionado con la pregunta, `main.py` devuelve un mensaje fijo sin llamar al
proveedor LLM (ver `NO_CONTEXT_MESSAGE` en `app/main.py`). El system prompt además
instruye al modelo a no completar con conocimiento propio ni siquiera cuando el
contexto encontrado es parcial.

Todo el material de `context/` viene de libros reales publicados (ver abajo) — ya no
hay archivos de ejemplo escritos a mano. Los dos que existían al principio del
proyecto (`cinematica_mru.txt`, `leyes_de_newton.txt`) se retiraron una vez que los
libros reales cubrieron esos mismos temas con más rigor: por ser cortos y muy
enfocados, le ganaban en el ranking a capítulos de libro completos incluso cuando el
capítulo real explicaba mejor — encontrado en la práctica con una pregunta sobre
movimiento rectilíneo que salió mal precisamente por esto.

> **Limitación conocida**: la selección de contexto es naive (TF-IDF simplificado,
> sin embeddings — ver `ARCHITECTURE.md`). Una pregunta genuinamente cubierta por el
> material, pero formulada con vocabulario distinto al de los archivos de `context/`,
> puede no encontrar coincidencias y rechazarse igual — falso negativo, no falso
> positivo. Se prefirió este trade-off explícitamente: es preferible que rechace una
> pregunta que sí podría responder, a que responda algo sin respaldo documental.

## Cómo funciona la selección (resumen técnico)

Con el corpus original (2-3 archivos chicos y temáticos), alcanzaba con contar
cuántas palabras clave compartían la pregunta y cada archivo. Al crecer el corpus a
~100 archivos (4 libros universitarios completos, ver abajo), ese conteo simple dejó
de alcanzar por dos motivos, encontrados en la práctica al integrar estos libros:

1. **Empates frecuentes.** Muchos archivos podían compartir la misma cantidad de
   palabras clave con la pregunta, y el desempate cae en orden alfabético de archivo
   — no en relevancia real.
2. **Palabras "comunes" en Física dejan de discriminar.** Con un solo libro chico,
   "fuerza" o "ley" ya alcanzaban para apuntar al archivo correcto. Con 4 libros
   completos, esas palabras aparecen en decenas de archivos distintos y no aportan
   señal.

Se pasó a **TF-IDF simplificado**: cada palabra clave de la pregunta pesa según qué
tan seguido aparece en el archivo candidato (frecuencia del término, normalizada por
el largo del archivo) y qué tan poco frecuente es esa palabra en el resto del corpus
(frecuencia inversa de documento). Esto hace que una palabra específica como
"refracción" pese mucho más que una genérica como "fuerza", y que un archivo chico y
enfocado en el tema (ej. `leyes_de_newton.txt`) le gane a un capítulo de libro entero
donde esa misma palabra aparece de pasada.

Además, con un corpus tan grande, **casi cualquier pregunta comparte alguna palabra
con algún archivo por pura coincidencia estadística** (se probó explícitamente: "¿Cómo
preparo un asado?" matcheaba algo antes de este cambio). Por eso se agregó
`MIN_CONTEXT_SCORE` (`app/config.py`): un piso de score por debajo del cual se
considera que no hay contexto relevante, aunque técnicamente haya alguna coincidencia.
Se calibró a mano comparando el score máximo de preguntas claramente de Física contra
preguntas claramente ajenas. Valor actual: `0.003`. **Si el corpus de `context/` cambia
mucho de tamaño, hay que volver a correr esta comparación y ajustar el valor** — no es
una constante física, es una calibración empírica contra el corpus actual.

> **Límite real de este enfoque (no es cuestión de afinar el número)**: TF-IDF cuenta
> palabras, no entiende su sentido. "¿Cuál es el río más largo del mundo?" (geografía)
> puntúa alto contra capítulos de "movimiento en dos dimensiones", porque esos
> capítulos usan seguido el problema clásico de un bote cruzando un río con corriente
> — la palabra "río" aparece mucho, en un sentido totalmente distinto. Ningún valor de
> `MIN_CONTEXT_SCORE` distingue eso; hace falta entender significado, no solo contar
> coincidencias (es, otra vez, el tipo de problema que resuelve RAG con embeddings).
> Comprobado en la práctica que el system prompt sí lo filtra en la capa siguiente
> (rechaza responder porque el contexto encontrado no cubre realmente la pregunta),
> así que la defensa real contra estos casos es la combinación de las dos capas, no el
> umbral solo.

Actualizar esta lista cada vez que se agregue un documento nuevo (ver
[README.md](../README.md#agregar-material-documental)).

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

## Libros universitarios completos

Se agregaron 4 libros de Física universitaria de nivel introductorio, cada uno
separado en un archivo por capítulo (mismo motivo que el libro anterior: un libro
completo en un solo archivo rompe la selección de contexto). Juntos cubren
prácticamente el temario completo de un curso introductorio: mecánica, oscilaciones
y ondas, termodinámica, electricidad y magnetismo, óptica, y una introducción a
relatividad especial. Son de nivel más avanzado que "La Física entre nosotros 5"
(pensado para Bachillerato) — el system prompt sigue pidiendo adaptar el lenguaje a
educación media independientemente de la fuente.

- **Serway** (`serway_capN_*.txt`, 22 archivos, prefijo `serway_`) — física
  universitaria general: medición y vectores, cinemática 1D/2D, leyes del
  movimiento, energía, cantidad de movimiento y colisiones, rotación y cuerpo
  rígido, momento angular, equilibrio estático y elasticidad, gravitación
  universal, mecánica de fluidos, oscilaciones, ondas mecánicas y sonoras,
  temperatura, primera ley de la termodinámica, teoría cinética de los gases,
  máquinas térmicas y entropía. Extracción limpia (PDF con capa de texto real, sin
  OCR).
- **Wilson** (`wilson_capN_*.txt`, 25 archivos, prefijo `wilson_`) — cobertura
  similar a Serway más un desarrollo más extenso de electricidad y magnetismo
  (cargas y campos eléctricos, potencial y capacitancia, corriente y resistencia,
  circuitos DC y AC, magnetismo, inducción y ondas electromagnéticas) y óptica
  (reflexión y refracción, espejos y lentes, óptica física/ondulatoria,
  instrumentos ópticos y visión). Nota: hay un desborde menor de contenido entre
  capítulos consecutivos (algunas páginas de un capítulo quedan al final del
  anterior), no corregido a mano.
- **Tipler-Mosca** (`tipler_capN_*.txt`, 21 archivos, prefijo `tipler_`) — física
  para ciencias e ingeniería, Volumen 1: medición, cinemática 1D/2D/3D, leyes de
  Newton y sus aplicaciones, trabajo y energía, conservación de la energía,
  momento lineal, rotación, momento angular, gravedad, equilibrio y elasticidad,
  fluidos, oscilaciones, movimiento ondulatorio y superposición de ondas,
  temperatura y teoría cinética, calor y primer principio, segundo principio, y
  una introducción a relatividad especial.
- **Feynman** (`feynman_capN_*.txt`, 18 archivos, prefijo `feynman_`) — Lecciones
  de Física, Vol. I (mecánica, radiación y calor), con el estilo más conceptual y
  menos formulario característico de Feynman: átomos y física básica, relación con
  otras ciencias, energía/tiempo/distancia, probabilidad, gravitación, movimiento,
  leyes de Newton y momentum, vectores, características de la fuerza, trabajo y
  energía potencial, movimiento browniano, teoría cinética, difusión y
  termodinámica, sonido, y una introducción a relatividad, rotación, oscilaciones
  y óptica. **Ojo**: el libro tiene 52 capítulos numerados, pero el OCR no marca
  cada uno con un encabezado propio en el cuerpo del texto (solo en el índice), así
  que la separación automática solo pudo ubicar 18 puntos de corte confiables —
  varios archivos agrupan varios capítulos consecutivos. Tres quedaron grandes
  (260-340K caracteres, muy por encima de `MAX_CONTEXT_CHARS`):
  `feynman_cap14_26_relatividad_rotacion_oscilaciones_optica.txt`,
  `feynman_cap27_35_optica_radiacion_polarizacion_vision.txt` y
  `feynman_cap36_40_vision_cuantica_gas_cinetico.txt`. Dentro de esos tres, la
  selección de contexto puede seguir devolviendo el inicio del archivo y no la
  sección exacta preguntada — pendiente de subdividir más si se nota que afecta
  respuestas reales.

Ningún libro de este grupo tenía una sección de solo-respuestas separable con
facilidad del resto del texto (a diferencia de "La Física entre nosotros 5"); no se
excluyó nada por ese motivo en estos 4.

> **Nota de calidad**: Serway y Tipler-Mosca tienen extracción limpia (PDFs con capa
> de texto). Wilson y Feynman muestran ruido de OCR ocasional (acentos inconsistentes,
> algún carácter mal reconocido), sin corregir a mano.
