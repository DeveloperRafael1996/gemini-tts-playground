"""Playground web interactivo para probar Google Gemini TTS con Gradio."""

import logging

import gradio as gr

from google_tts_demo.config import settings
from google_tts_demo.exceptions import TTSException
from google_tts_demo.pricing import AVAILABLE_MODELS
from google_tts_demo.profiles import (
    AVAILABLE_VOICES,
    DEFAULT_VOICE,
    get_profile,
    list_profiles,
    voice_gender,
)
from google_tts_demo.tts_service import GoogleTTSService

logger = logging.getLogger(__name__)

service = GoogleTTSService()

PROFILE_CHOICES = [(profile.display_name, profile.name) for profile in list_profiles()]
DEFAULT_PROFILE = "es-pe"

MODEL_CHOICES = AVAILABLE_MODELS
DEFAULT_MODEL = (
    settings.tts_model if settings.tts_model in MODEL_CHOICES else MODEL_CHOICES[0]
)

# Voces agrupadas por genero (Female primero, luego Male) y ordenadas
# alfabeticamente dentro de cada grupo, para poder identificarlas en la UI.
VOICE_CHOICES = [
    (f"{name} ({voice_gender(name)})", name)
    for name in sorted(AVAILABLE_VOICES, key=lambda name: (voice_gender(name), name))
]

DEFAULT_TEXT = (
    "Hola, soy tu asistente. Vamos a verificar tu identidad de forma segura. "
    "¿Puedes decirme tu nombre?"
)

QUICK_EXAMPLES = [
    [
        "es-pe",
        "Hola, soy tu asistente. Vamos a verificar tu identidad de forma segura. "
        "¿Puedes decirme tu nombre?",
    ],
    [
        "es-mx",
        "Hola, voy a acompañarte durante este proceso de verificación. "
        "Mira directamente a la cámara.",
    ],
    [
        "pt-br",
        "Olá, sou seu assistente. Vamos verificar sua identidade com segurança. "
        "Pode me dizer seu nome?",
    ],
    [
        "en-us",
        "Hello, I'm your assistant. We're going to verify your identity securely. "
        "Could you please tell me your name?",
    ],
]

COMPARISON_SLOTS = len(AVAILABLE_VOICES)
HISTORY_HEADERS = [
    "Profile",
    "Language",
    "Voice",
    "Gender",
    "Characters",
    "Time (s)",
    "Audio (s)",
    "Cost (USD)",
    "Filename",
]

MODAL_CSS = """
.request-modal-overlay {
    position: fixed !important;
    inset: 0;
    z-index: 1000;
    display: flex !important;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.6);
}
.request-modal-box {
    background: var(--background-fill-primary);
    border: 1px solid var(--border-color-primary);
    border-radius: 8px;
    padding: 20px;
    width: min(700px, 90vw);
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}
"""


def _char_count_label(text: str) -> str:
    return f"Characters: {len(text or '')}"


def _on_profile_change(profile_name: str) -> str:
    profile = get_profile(profile_name)
    return profile.prompt


def _load_example(profile_name: str, text: str) -> tuple[str, str, str]:
    profile = get_profile(profile_name)
    return profile_name, text, profile.prompt


def _generate_audio(
    profile_name: str,
    voice_name: str,
    model_name: str,
    text: str,
    prompt: str,
    history: list[list[str]],
):
    if not text or not text.strip():
        yield (
            "Error generating audio: text cannot be empty",
            None,
            None,
            "",
            history,
            history,
        )
        return

    yield "Generating audio...", None, None, "", history, history

    try:
        result = service.synthesize(
            text=text,
            profile_name=profile_name,
            voice_name=voice_name,
            custom_prompt=prompt,
            model_name=model_name,
        )
    except TTSException as exc:
        logger.exception("Error generating audio in playground")
        yield f"Error generating audio: {exc}", None, None, "", history, history
        return
    except Exception as exc:  # noqa: BLE001 - mostrar mensaje amigable, loguear detalle
        logger.exception("Unexpected error generating audio in playground")
        yield f"Error generating audio: {exc}", None, None, "", history, history
        return

    info = (
        f"**Profile:** {profile_name}\n\n"
        f"**Language:** {result.language_code}\n\n"
        f"**Voice:** {result.voice} ({voice_gender(result.voice)})\n\n"
        f"**Model:** {result.cost.model}\n\n"
        f"**Characters:** {len(text)}\n\n"
        f"**Generation time:** {result.duration_seconds:.2f}s\n\n"
        f"**Audio duration:** {result.audio_duration_seconds:.2f}s\n\n"
        f"**Cost:** ${result.cost.total_cost_usd:.6f} USD "
        f"(input: {result.cost.input_tokens} tok = ${result.cost.input_cost_usd:.6f}, "
        f"output: {result.cost.output_tokens} tok = ${result.cost.output_cost_usd:.6f})\n\n"
        f"**File:** {result.output_path}"
    )

    new_row = [
        profile_name,
        result.language_code,
        result.voice,
        voice_gender(result.voice),
        str(len(text)),
        f"{result.duration_seconds:.2f}",
        f"{result.audio_duration_seconds:.2f}",
        f"{result.cost.total_cost_usd:.6f}",
        result.output_path,
    ]
    updated_history = [*history, new_row]

    yield (
        "Audio generated successfully",
        result.output_path,
        result.output_path,
        info,
        updated_history,
        updated_history,
    )


def _compare_voices(
    profile_name: str,
    voice_names: list[str],
    model_name: str,
    text: str,
    prompt: str,
    history: list[list[str]],
):
    empty_updates = [gr.update(visible=False) for _ in range(COMPARISON_SLOTS)]

    if not text or not text.strip():
        message = "Error generating audio: text cannot be empty"
        yield message, *empty_updates, history, history
        return

    if not voice_names:
        yield "Select at least one voice to compare", *empty_updates, history, history
        return

    yield "Generating audio...", *empty_updates, history, history

    try:
        results = service.synthesize_many(
            text=text,
            profile_name=profile_name,
            voice_names=voice_names,
            custom_prompt=prompt,
            model_name=model_name,
        )
    except TTSException as exc:
        logger.exception("Error comparing voices in playground")
        yield f"Error generating audio: {exc}", *empty_updates, history, history
        return
    except Exception as exc:  # noqa: BLE001 - mostrar mensaje amigable, loguear detalle
        logger.exception("Unexpected error comparing voices in playground")
        yield f"Error generating audio: {exc}", *empty_updates, history, history
        return

    updates = []
    new_rows = []
    for i in range(COMPARISON_SLOTS):
        if i < len(results):
            result = results[i]
            gender = voice_gender(result.voice)
            updates.append(
                gr.update(
                    visible=True,
                    value=result.output_path,
                    label=(
                        f"{result.voice} ({gender}, {result.language_code}, "
                        f"{result.duration_seconds:.2f}s, "
                        f"${result.cost.total_cost_usd:.6f})"
                    ),
                )
            )
            new_rows.append(
                [
                    profile_name,
                    result.language_code,
                    result.voice,
                    gender,
                    str(len(text)),
                    f"{result.duration_seconds:.2f}",
                    f"{result.audio_duration_seconds:.2f}",
                    f"{result.cost.total_cost_usd:.6f}",
                    result.output_path,
                ]
            )
        else:
            updates.append(gr.update(visible=False))

    updated_history = [*history, *new_rows]

    yield "Audio generated successfully", *updates, updated_history, updated_history


def _preview_single_request(
    profile_name: str,
    voice_name: str,
    model_name: str,
    text: str,
    prompt: str,
):
    payload = service.build_request_payload(
        text=text,
        profile_name=profile_name,
        voice_name=voice_name,
        custom_prompt=prompt,
        model_name=model_name,
    )
    return payload, gr.update(visible=True)


def _preview_compare_requests(
    profile_name: str,
    voice_names: list[str],
    model_name: str,
    text: str,
    prompt: str,
):
    payloads = [
        service.build_request_payload(
            text=text,
            profile_name=profile_name,
            voice_name=voice_name,
            custom_prompt=prompt,
            model_name=model_name,
        )
        for voice_name in (voice_names or [])
    ]
    return {"requests": payloads}, gr.update(visible=True)


def _close_request_modal():
    return gr.update(visible=False)


def build_interface() -> gr.Blocks:
    """Construye la interfaz de Gradio del Playground."""
    with gr.Blocks(title="Google Gemini TTS Playground") as demo:
        gr.Markdown("# Google Gemini TTS Playground")
        gr.Markdown("Try languages, accents, voices, and styles using Google Cloud Gemini TTS.")

        history_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Configuration")

                profile_dropdown = gr.Dropdown(
                    choices=PROFILE_CHOICES,
                    value=DEFAULT_PROFILE,
                    label="Language / Profile",
                )
                model_dropdown = gr.Dropdown(
                    choices=MODEL_CHOICES,
                    value=DEFAULT_MODEL,
                    label="Model",
                )
                text_box = gr.Textbox(
                    label="Text",
                    value=DEFAULT_TEXT,
                    lines=6,
                )
                char_count = gr.Markdown(_char_count_label(DEFAULT_TEXT))

                with gr.Accordion("Voice Prompt / Style (advanced)", open=False):
                    prompt_box = gr.Textbox(
                        label="Voice Prompt / Style",
                        value=get_profile(DEFAULT_PROFILE).prompt,
                        lines=6,
                        show_label=False,
                    )

                gr.Markdown("### Quick test cases")
                gr.Examples(
                    examples=QUICK_EXAMPLES,
                    inputs=[profile_dropdown, text_box],
                    outputs=[profile_dropdown, text_box, prompt_box],
                    fn=_load_example,
                    run_on_click=True,
                    label="Examples by language",
                )

            with gr.Column(scale=1):
                with gr.Tabs():
                    with gr.Tab("Generate"):
                        voice_dropdown = gr.Dropdown(
                            choices=VOICE_CHOICES,
                            value=DEFAULT_VOICE,
                            label="Voice (grouped by gender)",
                        )
                        with gr.Row():
                            generate_btn = gr.Button("Generate Audio", variant="primary")
                            preview_btn = gr.Button("Preview SDK Request (JSON)")
                        status_md = gr.Markdown("")
                        audio_player = gr.Audio(label="Result", type="filepath")
                        download_file = gr.File(label="Download MP3")
                        info_md = gr.Markdown("")

                    with gr.Tab("Compare Voices"):
                        comparison_voices = gr.Dropdown(
                            choices=VOICE_CHOICES,
                            value=["Kore", "Aoede", "Leda", "Charon"],
                            multiselect=True,
                            label="Voices to compare (grouped by gender)",
                        )
                        with gr.Row():
                            compare_btn = gr.Button("Compare Voices", variant="primary")
                            compare_preview_btn = gr.Button("Preview SDK Requests (JSON)")
                        compare_status = gr.Markdown("")

                        comparison_audios = []
                        with gr.Row():
                            for _ in range(COMPARISON_SLOTS):
                                audio = gr.Audio(label="", type="filepath", visible=False)
                                comparison_audios.append(audio)

                    with gr.Tab("History"):
                        history_table = gr.Dataframe(
                            headers=HISTORY_HEADERS,
                            datatype=["str"] * len(HISTORY_HEADERS),
                            row_count=(0, "dynamic"),
                            column_count=(len(HISTORY_HEADERS), "fixed"),
                            value=[],
                        )

        with gr.Group(visible=False, elem_classes="request-modal-overlay") as request_modal:
            with gr.Column(elem_classes="request-modal-box"):
                gr.Markdown("### SDK Request Payload")
                request_json = gr.JSON(label="")
                close_modal_btn = gr.Button("Close")

        text_box.change(_char_count_label, inputs=text_box, outputs=char_count)
        profile_dropdown.change(_on_profile_change, inputs=profile_dropdown, outputs=prompt_box)

        generate_btn.click(
            _generate_audio,
            inputs=[
                profile_dropdown,
                voice_dropdown,
                model_dropdown,
                text_box,
                prompt_box,
                history_state,
            ],
            outputs=[
                status_md,
                audio_player,
                download_file,
                info_md,
                history_state,
                history_table,
            ],
        )

        compare_btn.click(
            _compare_voices,
            inputs=[
                profile_dropdown,
                comparison_voices,
                model_dropdown,
                text_box,
                prompt_box,
                history_state,
            ],
            outputs=[compare_status, *comparison_audios, history_state, history_table],
        )

        preview_btn.click(
            _preview_single_request,
            inputs=[profile_dropdown, voice_dropdown, model_dropdown, text_box, prompt_box],
            outputs=[request_json, request_modal],
        )

        compare_preview_btn.click(
            _preview_compare_requests,
            inputs=[profile_dropdown, comparison_voices, model_dropdown, text_box, prompt_box],
            outputs=[request_json, request_modal],
        )

        close_modal_btn.click(_close_request_modal, outputs=[request_modal])

    return demo


# Modulo-level: requerido por `gradio` en modo watch/reload para poder
# localizar y reemplazar la interfaz cuando cambian los archivos fuente.
demo = build_interface()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings.ensure_output_dir()
    print("Google Gemini TTS Playground\n")
    print(f"Running on:\n\nhttp://{settings.playground_host}:{settings.playground_port}\n")
    demo.launch(
        server_name=settings.playground_host,
        server_port=settings.playground_port,
        css=MODAL_CSS,
    )


if __name__ == "__main__":
    main()
