# Google Gemini TTS Demo

Proyecto Python para probar **Google Cloud Text-to-Speech** utilizando **Gemini 2.5 Flash TTS**,
con soporte para múltiples idiomas, acentos y estilos de voz (prioridad en español y portugués
latinoamericanos), una CLI para generar audio por línea de comandos y un **Playground web**
interactivo (Gradio) para generar, comparar y escuchar los audios.

Gestionado 100% con [`uv`](https://docs.astral.sh/uv/) (sin `pip`, `poetry`, `pipenv` ni
`requirements.txt`).

## 1. Qué hace el proyecto

- Genera archivos MP3 a partir de texto usando Google Cloud TTS + modelo Gemini TTS.
- Permite elegir perfil de idioma/acento (español LatAm, Perú, México, Colombia, Argentina,
  portugués de Brasil/São Paulo/Río, inglés US/UK/con acento latino).
- Permite elegir voz (Kore, Aoede, Leda, Charon, Puck, Fenrir, Zephyr, Achernar, Schedar, Sulafat).
- Permite editar el "Voice Prompt" (estilo, tono, acento, formalidad) antes de generar el audio.
- Permite comparar el mismo texto/perfil con varias voces (A/B testing).
- Guarda todos los MP3 en `outputs/` con nombres únicos.

## 2. Arquitectura

```text
CLI (main.py) ──────────┐
                         ▼
                  GoogleTTSService (tts_service.py)
                         │
                         ▼
                  Google Cloud TTS (Gemini TTS)
                         ▲
                         │
Playground (playground.py) ───┘
```

- `config.py`: configuración vía `pydantic-settings` (proyecto GCP, modelo, voz por defecto,
  directorio de salida, host/puerto del Playground).
- `models.py`: modelos Pydantic (`TTSProfile`, `TTSRequest`, `TTSResult`).
- `profiles.py`: registro centralizado de perfiles de idioma/acento y de la lista de voces
  disponibles (una única fuente de verdad, reutilizada por CLI y Playground).
- `tts_service.py`: **único** punto de integración con Google Cloud TTS (`GoogleTTSService`).
  Tanto la CLI como el Playground lo utilizan; la lógica de síntesis no está duplicada.
- `main.py`: CLI basada en `argparse`.
- `playground.py`: interfaz web con Gradio, construida sobre `GoogleTTSService`.
- `exceptions.py`: excepciones del dominio (`TTSException`, `TTSProfileNotFoundError`,
  `TTSSynthesisError`).

## 3. Instalación de uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verifica la instalación:

```bash
uv --version
```

## 4. Instalación de dependencias

```bash
uv sync
```

Esto crea el entorno virtual `.venv` e instala todas las dependencias declaradas en
`pyproject.toml` (no existe `requirements.txt`).

## 5. Configuración de Google Cloud (GCP)

1. Crea o selecciona un proyecto en Google Cloud.
2. Habilita la API **Cloud Text-to-Speech**.
3. Asegúrate de tener acceso al modelo Gemini TTS (`gemini-2.5-flash-tts`) en tu proyecto.

## 6. Autenticación

```bash
gcloud auth application-default login
gcloud config set project PROJECT_ID
```

Las credenciales de Application Default Credentials (ADC) son utilizadas automáticamente por
`google-cloud-texttospeech`. No es necesario ni recomendable guardar credenciales en el
repositorio.

## 7. Variables de entorno

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

Variables disponibles:

| Variable               | Descripción                              | Valor por defecto      |
|-------------------------|-------------------------------------------|-------------------------|
| `GOOGLE_CLOUD_PROJECT`  | ID del proyecto de Google Cloud            | *(vacío)*               |
| `TTS_MODEL`             | Modelo Gemini TTS a utilizar               | `gemini-2.5-flash-tts`  |
| `TTS_DEFAULT_VOICE`     | Voz por defecto                            | `Kore`                  |
| `TTS_OUTPUT_DIR`        | Carpeta donde se guardan los MP3           | `outputs`               |
| `PLAYGROUND_HOST`       | Host del Playground web                    | `127.0.0.1`             |
| `PLAYGROUND_PORT`       | Puerto del Playground web                  | `7860`                  |

## 8. Uso mediante CLI

Listar perfiles disponibles:

```bash
uv run python -m google_tts_demo.main --list-profiles
```

Generar audio (español, Perú):

```bash
uv run python -m google_tts_demo.main \
    --profile es-pe \
    --text "Hola, soy tu asistente. ¿Puedes decirme tu nombre?"
```

Portugués:

```bash
uv run python -m google_tts_demo.main \
    --profile pt-br \
    --text "Olá, sou seu assistente. Pode me dizer seu nome?"
```

Inglés:

```bash
uv run python -m google_tts_demo.main \
    --profile en-us \
    --text "Hello, I'm your assistant. Could you tell me your name?"
```

Elegir una voz específica o un nombre de archivo:

```bash
uv run python -m google_tts_demo.main \
    --profile es-pe \
    --voice Aoede \
    --text "Hola" \
    --output mi_audio.mp3
```

### Comparación A/B de voces (CLI)

```bash
uv run python -m google_tts_demo.main \
    --profile es-pe \
    --text "Hola, soy tu asistente." \
    --voices Kore,Aoede,Leda,Charon
```

Genera:

```text
outputs/es-pe_Kore_<timestamp>.mp3
outputs/es-pe_Aoede_<timestamp>.mp3
outputs/es-pe_Leda_<timestamp>.mp3
outputs/es-pe_Charon_<timestamp>.mp3
```

## 9. Uso mediante el Playground web

```bash
uv run python -m google_tts_demo.playground
```

Abre en el navegador:

```text
http://127.0.0.1:7860
```

### Seleccionar idioma / acento

En el dropdown **Idioma / Perfil**, elige entre Español Latinoamérica, Perú, México, Colombia,
Argentina, Português Brasil/São Paulo/Rio, English US/UK/Latin Accent.

### Seleccionar voz

En el dropdown **Voice**, elige entre las voces centralizadas en `profiles.py`
(Kore por defecto).

### Personalizar el prompt

Al cambiar de perfil, el campo **Voice Prompt / Style** se actualiza automáticamente con el
prompt sugerido para ese acento. Puedes editarlo libremente antes de generar el audio para
experimentar con acento, tono, emoción, velocidad, formalidad y naturalidad.

### Generar y escuchar audio

1. Escribe o edita el texto (el contador de caracteres se actualiza en vivo).
2. Ajusta el Voice Prompt si lo deseas.
3. Pulsa **Generate Audio**.
4. El estado muestra `Generating audio...` y luego `Audio generated successfully`.
5. El reproductor de audio permite escuchar el resultado inmediatamente.
6. El componente de descarga permite obtener el MP3 generado (guardado también en `outputs/`).
7. Se muestra información técnica: Profile, Language, Voice, Model, Characters, File.

### Comparar voces

En la sección **Voice Comparison**, selecciona varias voces (multiselección), pulsa
**Compare Voices** y escucha cada resultado de forma independiente (los audios no se
reproducen automáticamente).

### Casos de prueba rápidos

La sección de ejemplos permite cargar textos predefinidos (identidad, portugués, inglés) y
ejemplos orientados a un asistente de onboarding/biometría (acercar el rostro, retirar lentes,
una sola persona frente a cámara, iluminación, captura correcta/incorrecta).

### Historial de la sesión

Una tabla registra Profile, Language, Voice, Characters y Filename de cada audio generado
durante la sesión actual del Playground (en memoria, sin base de datos).

## 10. Ubicación de los MP3 generados

Todos los archivos se guardan en `outputs/` con el formato:

```text
{profile}_{voice}_{timestamp}.mp3
```

Ejemplo: `outputs/es-pe_Kore_20260921_155500.mp3`.

## 11. Ejecutar tests

```bash
uv run pytest
```

Los tests usan mocks (`pytest-mock` / `unittest.mock`) para el cliente de Google Cloud TTS: no
se realiza ninguna llamada real a la API de Google en la suite de tests.

## 12. Ejecutar Ruff

Lint:

```bash
uv run ruff check .
```

Formato:

```bash
uv run ruff format .
```

## 13. Resumen de comandos

```bash
uv sync
uv run python -m google_tts_demo.playground
uv run python -m google_tts_demo.main --profile es-pe --text "Hola"
uv run pytest
uv run ruff check .
uv run ruff format .
```
