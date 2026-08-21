# Guía de instalación local (paso a paso, sin experiencia técnica)

Esta guía es para instalar y correr el chatbot en tu propia computadora — para
probarlo, mostrarlo o experimentar con el material, sin depender del sitio en
producción. No hace falta saber programar, pero sí vas a usar una terminal (una
ventana donde se escriben comandos en vez de hacer clic). Cubre **Windows** y
**Ubuntu**; donde los pasos difieren, están separados con claridad.

Si en algún paso el resultado no se parece a lo que describe la guía, pará ahí y
pedí ayuda (ver el final del documento) en vez de seguir probando cosas al azar.

## Antes de empezar (se hace una sola vez)

### 1. Instalar Python

**Windows**: entrá a [python.org/downloads](https://www.python.org/downloads/) y
descargá la versión más reciente. Al instalar, es importante tildar la casilla
**"Add python.exe to PATH"** en la primera pantalla del instalador — si te la
salteás, los comandos de más abajo no van a funcionar y vas a tener que reinstalar.

**Ubuntu**: Python ya viene instalado, pero probablemente falten dos paquetes.
Abrí una terminal y ejecutá:
```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

### 2. Descargar el código del proyecto

La forma más simple, sin instalar nada más:
1. Andá a la página del proyecto en GitHub:
   https://github.com/kterva/chatbot-fisica
2. Botón verde **"Code"** → **"Download ZIP"**.
3. Descomprimí el archivo en una carpeta que puedas encontrar fácil (ej.
   Escritorio o Documentos). Vas a terminar con una carpeta llamada
   `chatbot-fisica` (o `chatbot-fisica-main`).

### 3. Abrir una terminal dentro de esa carpeta

**Windows**: abrí el Explorador de archivos, entrá a la carpeta del proyecto, y en
la barra de direcciones (arriba, donde dice la ruta) escribí `powershell` y
apretá Enter. Se abre una terminal ya ubicada ahí.

**Ubuntu**: abrí la carpeta con el explorador de archivos, clic derecho dentro de
la carpeta → **"Abrir en terminal"**.

### 4. Crear el entorno virtual (una sola vez)

Un "entorno virtual" es una carpeta aislada donde se instalan las dependencias del
proyecto, para no mezclarlas con otras cosas de tu computadora. Desde la terminal
que abriste:

```bash
cd backend
```

**Windows**:
```powershell
python -m venv .venv
```

**Ubuntu**:
```bash
python3 -m venv .venv
```

Esto tarda unos segundos y no muestra casi nada en pantalla — es normal.

### 5. Activar el entorno virtual

Hay que hacer esto **cada vez** que abras una terminal nueva para trabajar con el
proyecto (no solo la primera vez).

**Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
```
Si aparece un error sobre "ejecución de scripts deshabilitada", ejecutá primero
esto (una sola vez) y volvé a intentar:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Ubuntu**:
```bash
source .venv/bin/activate
```

Si funcionó, vas a ver `(.venv)` al principio de la línea de la terminal. Si no
aparece, algo falló — no sigas al siguiente paso.

### 6. Instalar las dependencias (una sola vez)

Con el entorno activado (tiene que decir `(.venv)`):
```bash
pip install -r requirements.txt
```
Tarda unos minutos y muestra bastante texto — es normal, dejalo terminar.

### 7. Conseguir una clave de acceso (API key) gratuita

El chatbot necesita conectarse a un proveedor de IA para generar respuestas. Usamos
NVIDIA NIM, que tiene una capa gratuita:

1. Entrá a [build.nvidia.com](https://build.nvidia.com) y creá una cuenta.
2. Una vez adentro, generá una API key (aparece la opción entrando a cualquier
   modelo del catálogo).
3. Copiá esa clave — es un texto largo que empieza con `nvapi-`. **Es personal y
   privada**: no la compartas ni la subas a ningún lado.

### 8. Configurar la clave en el proyecto

Todavía dentro de la carpeta `backend`:

**Windows**:
```powershell
copy .env.example .env
```

**Ubuntu**:
```bash
cp .env.example .env
```

Ahora abrí el archivo `.env` que se creó (está dentro de la carpeta `backend`) con
un editor de texto simple (Bloc de notas en Windows, gedit o Texto en Ubuntu — no
hace falta nada especial). Buscá la línea:
```
NVIDIA_API_KEY=
```
y pegá tu clave justo después del `=`, sin espacios ni comillas:
```
NVIDIA_API_KEY=nvapi-tu-clave-pegada-acá
```
Guardá el archivo y cerralo.

## Cada vez que quieras usar el chatbot

Una vez hecho todo lo anterior, para volver a usarlo no hay que repetir todos los
pasos — solo:

1. Abrí una terminal dentro de la carpeta `backend` (paso 3).
2. Activá el entorno virtual (paso 5) — tiene que aparecer `(.venv)`.
3. Arrancá el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Abrí el navegador en **http://localhost:8000/**
5. Para cerrar todo: volvé a la terminal y apretá `Ctrl+C`. Cerrar la ventana del
   navegador no alcanza, el servidor sigue corriendo hasta que lo pares ahí.

## Agregar más material (PDFs) al chatbot

El chatbot solo responde con lo que hay en la carpeta `context/` — para que pueda
usar un libro o apunte nuevo, primero hay que convertir ese PDF a texto plano ahí
adentro. Hay un script que lo hace automáticamente.

1. Copiá el o los PDF nuevos dentro de la carpeta `documents/` (está en la raíz del
   proyecto, al lado de `backend/`, `context/`, etc.).
2. Abrí una terminal y activá el entorno virtual como en el paso 5 de más arriba
   (tiene que aparecer `(.venv)`). Si estás parado en la carpeta `backend`, salí un
   nivel:
   ```bash
   cd ..
   ```
3. Ejecutá:
   ```bash
   python scripts/extract_pdf_text.py
   ```
   Esto procesa **todos** los PDF que haya en `documents/` (no solo el nuevo) y
   genera un archivo `.txt` por cada uno dentro de `context/`, con el mismo nombre
   que el PDF. Si preferís convertir uno solo:
   ```bash
   python scripts/extract_pdf_text.py nombre-del-archivo.pdf
   ```
4. Los archivos `.txt` que aparecen en `context/` son los que el chatbot usa — no
   hace falta reiniciar el servidor, el cambio se ve en la siguiente pregunta que
   hagas.

**Importante — PDF escaneados**: este script solo funciona con PDF que tienen texto
real adentro (el que se puede seleccionar y copiar con el mouse en un lector de
PDF). Si el PDF es un escaneo (páginas fotografiadas o escaneadas, sin texto
seleccionable), el script va a avisar "no se pudo extraer texto" y no va a generar
nada — para esos casos hace falta un proceso de reconocimiento de texto (OCR)
distinto, que no está automatizado en este proyecto. Si te encontrás con esto,
pedí ayuda en vez de intentar forzarlo.

## Problemas frecuentes

- **"python no se reconoce como un comando" / "command not found: python3"** — Python
  no quedó instalado o no se agregó al PATH (paso 1). Reinstalá prestando atención a
  esa casilla.
- **El error menciona "Address already in use" o el puerto 8000 ocupado** — ya hay
  otro proceso usando ese puerto (quizás una terminal anterior que no cerraste).
  Cerrá esa terminal, o arrancá con `uvicorn app.main:app --reload --port 8001` y
  abrí `http://localhost:8001/` en su lugar.
- **El chatbot responde siempre con un error genérico** — revisá que la clave en
  `.env` esté bien pegada, sin espacios extra ni comillas, y que el archivo se
  llame exactamente `.env` (no `.env.txt`).
- **La página no carga en el navegador** — fijate que la terminal siga mostrando el
  servidor corriendo (no se cerró solo ni dio un error), y que la dirección sea
  exactamente `http://localhost:8000/`.

## Si nada de esto funciona

Mandá el mensaje de error completo (una captura de pantalla de la terminal ayuda
mucho), en qué paso pasó, y si es Windows o Ubuntu.
