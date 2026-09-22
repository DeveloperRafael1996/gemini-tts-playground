"""Servicio unico de integracion con Google Cloud Text-to-Speech (Gemini TTS)."""

import logging
import re
import time
from datetime import datetime
from pathlib import Path

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import texttospeech
from mutagen.mp3 import MP3

from google_tts_demo.config import Settings, settings
from google_tts_demo.exceptions import TTSSynthesisError
from google_tts_demo.models import TTSResult
from google_tts_demo.pricing import calculate_cost
from google_tts_demo.profiles import get_profile

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


def _sanitize_filename_part(value: str) -> str:
    """Sanitiza un fragmento de nombre de archivo reemplazando caracteres invalidos."""
    return _UNSAFE_FILENAME_CHARS.sub("_", value).strip("_")


def _get_mp3_duration_seconds(path: Path) -> float:
    """Lee la duracion real (en segundos) de un archivo MP3.

    Devuelve 0.0 si el archivo no es un MP3 valido (p. ej. en tests con datos falsos),
    en lugar de fallar la sintesis por un problema de calculo de costo.
    """
    try:
        return MP3(path).info.length
    except Exception:
        logger.warning("No se pudo leer la duracion del audio en %s", path, exc_info=True)
        return 0.0


def _build_filename(profile_name: str, voice_name: str) -> str:
    """Construye un nombre de archivo unico: {profile}_{voice}_{timestamp}.mp3."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_profile = _sanitize_filename_part(profile_name)
    safe_voice = _sanitize_filename_part(voice_name)
    return f"{safe_profile}_{safe_voice}_{timestamp}.mp3"


class GoogleTTSService:
    """Punto unico de integracion con Google Cloud TTS / Gemini TTS.

    Tanto la CLI como el Playground deben utilizar esta clase para
    evitar duplicar la logica de sintesis de audio.
    """

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings
        self._client: texttospeech.TextToSpeechClient | None = None

    @property
    def client(self) -> texttospeech.TextToSpeechClient:
        """Cliente de Google Cloud TTS, creado de forma perezosa."""
        if self._client is None:
            self._client = texttospeech.TextToSpeechClient()
        return self._client

    def build_request_payload(
        self,
        text: str,
        profile_name: str,
        voice_name: str | None = None,
        custom_prompt: str | None = None,
        model_name: str | None = None,
    ) -> dict:
        """Construye el payload (JSON-serializable) que se enviara al SDK de Google Cloud TTS.

        Refleja exactamente los parametros usados en `synthesize()`, para poder
        previsualizar la solicitud sin llamar a la API.
        """
        profile = get_profile(profile_name)
        resolved_voice = voice_name or profile.voice_name
        resolved_prompt = custom_prompt if custom_prompt is not None else profile.prompt

        return {
            "input": {
                "text": text,
                "prompt": resolved_prompt,
            },
            "voice": {
                "language_code": profile.language_code,
                "name": resolved_voice,
                "model_name": model_name or self._settings.tts_model,
            },
            "audio_config": {
                "audio_encoding": "MP3",
                "pitch": 0.0,
                "speaking_rate": 1.0,
            },
        }

    def synthesize(
        self,
        text: str,
        profile_name: str,
        output_filename: str | None = None,
        voice_name: str | None = None,
        custom_prompt: str | None = None,
        model_name: str | None = None,
    ) -> TTSResult:
        """Genera un archivo MP3 a partir de texto usando Gemini TTS.

        Lanza TTSProfileNotFoundError si el perfil no existe y
        TTSSynthesisError si falla la llamada a Google Cloud TTS.
        """
        profile = get_profile(profile_name)
        payload = self.build_request_payload(
            text=text,
            profile_name=profile_name,
            voice_name=voice_name,
            custom_prompt=custom_prompt,
            model_name=model_name,
        )
        resolved_voice = payload["voice"]["name"]

        synthesis_input = texttospeech.SynthesisInput(
            text=payload["input"]["text"],
            prompt=payload["input"]["prompt"],
        )
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=payload["voice"]["language_code"],
            name=payload["voice"]["name"],
            model_name=payload["voice"]["model_name"],
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=payload["audio_config"]["pitch"],
            speaking_rate=payload["audio_config"]["speaking_rate"],
        )

        logger.info(
            "Synthesizing audio: profile=%s voice=%s language_code=%s characters=%d",
            profile_name,
            resolved_voice,
            profile.language_code,
            len(text),
        )

        start_time = time.perf_counter()
        try:
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )
        except GoogleAPICallError as exc:
            logger.exception("Google Cloud TTS synthesis failed")
            raise TTSSynthesisError(f"Fallo la sintesis de audio: {exc}") from exc
        duration_seconds = time.perf_counter() - start_time

        output_dir = self._settings.ensure_output_dir()
        filename = output_filename or _build_filename(profile_name, resolved_voice)
        output_path = output_dir / filename
        output_path.write_bytes(response.audio_content)

        audio_duration_seconds = _get_mp3_duration_seconds(output_path)
        cost = calculate_cost(
            text=text,
            audio_duration_seconds=audio_duration_seconds,
            model_name=payload["voice"]["model_name"],
        )

        logger.info(
            "Audio saved to %s (generation took %.2fs, audio %.2fs, cost $%.6f)",
            output_path,
            duration_seconds,
            audio_duration_seconds,
            cost.total_cost_usd,
        )

        return TTSResult(
            profile=profile_name,
            voice=resolved_voice,
            language_code=profile.language_code,
            output_path=str(output_path),
            duration_seconds=duration_seconds,
            audio_duration_seconds=audio_duration_seconds,
            cost=cost,
        )

    def synthesize_many(
        self,
        text: str,
        profile_name: str,
        voice_names: list[str],
        custom_prompt: str | None = None,
        model_name: str | None = None,
    ) -> list[TTSResult]:
        """Genera el mismo texto/perfil/prompt con varias voces para comparacion A/B."""
        results = []
        for voice_name in voice_names:
            result = self.synthesize(
                text=text,
                profile_name=profile_name,
                voice_name=voice_name,
                custom_prompt=custom_prompt,
                model_name=model_name,
            )
            results.append(result)
        return results
