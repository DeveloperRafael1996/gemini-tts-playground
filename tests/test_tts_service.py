"""Tests para GoogleTTSService. No debe realizar llamadas reales a Google Cloud."""

import re
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from google_tts_demo.config import Settings
from google_tts_demo.exceptions import TTSSynthesisError
from google_tts_demo.tts_service import GoogleTTSService, _build_filename


@pytest.fixture
def fake_settings(tmp_path) -> Settings:
    return Settings(
        google_cloud_project="test-project",
        tts_model="gemini-2.5-flash-tts",
        tts_default_voice="Kore",
        tts_output_dir=tmp_path / "outputs",
    )


@pytest.fixture
def service(fake_settings) -> GoogleTTSService:
    svc = GoogleTTSService(app_settings=fake_settings)
    fake_client = MagicMock()
    fake_client.synthesize_speech.return_value = MagicMock(audio_content=b"fake-mp3-bytes")
    svc._client = fake_client
    return svc


def test_synthesize_writes_mp3_and_returns_result(service, fake_settings) -> None:
    result = service.synthesize(text="Hola mundo", profile_name="es-pe")

    assert result.profile == "es-pe"
    assert result.voice == "Kore"
    assert result.language_code == "es-419"

    output_path = fake_settings.tts_output_dir / result.output_path.split("/")[-1]
    assert output_path.exists()
    assert output_path.read_bytes() == b"fake-mp3-bytes"


def test_synthesize_uses_profile_prompt_by_default(service) -> None:
    service.synthesize(text="Hola", profile_name="es-pe")

    call_kwargs = service.client.synthesize_speech.call_args.kwargs
    assert "peruano" in call_kwargs["input"].prompt.lower()


def test_synthesize_with_custom_prompt_overrides_profile_prompt(service) -> None:
    service.synthesize(text="Hola", profile_name="es-pe", custom_prompt="Estilo personalizado")

    call_kwargs = service.client.synthesize_speech.call_args.kwargs
    assert call_kwargs["input"].prompt == "Estilo personalizado"


def test_synthesize_with_custom_voice_overrides_profile_voice(service) -> None:
    result = service.synthesize(text="Hola", profile_name="es-pe", voice_name="Aoede")

    assert result.voice == "Aoede"
    call_kwargs = service.client.synthesize_speech.call_args.kwargs
    assert call_kwargs["voice"].name == "Aoede"


def test_synthesize_unknown_profile_raises(service) -> None:
    from google_tts_demo.exceptions import TTSProfileNotFoundError

    with pytest.raises(TTSProfileNotFoundError):
        service.synthesize(text="Hola", profile_name="does-not-exist")


def test_synthesize_wraps_google_api_error(service) -> None:
    service.client.synthesize_speech.side_effect = GoogleAPICallError("boom")

    with pytest.raises(TTSSynthesisError):
        service.synthesize(text="Hola", profile_name="es-pe")


def test_synthesize_creates_output_directory(service, fake_settings) -> None:
    assert not fake_settings.tts_output_dir.exists()

    service.synthesize(text="Hola", profile_name="es-pe")

    assert fake_settings.tts_output_dir.exists()


def test_build_filename_format_and_uniqueness() -> None:
    filename = _build_filename("es-pe", "Kore")

    assert re.match(r"^es-pe_Kore_\d{8}_\d{6}\.mp3$", filename)


def test_synthesize_uses_explicit_output_filename(service, fake_settings) -> None:
    result = service.synthesize(
        text="Hola", profile_name="es-pe", output_filename="custom_name.mp3"
    )

    assert result.output_path.endswith("custom_name.mp3")
    assert (fake_settings.tts_output_dir / "custom_name.mp3").exists()


def test_synthesize_many_generates_result_per_voice(service) -> None:
    voices = ["Kore", "Aoede", "Leda", "Charon"]

    results = service.synthesize_many(
        text="Hola, soy tu asistente.",
        profile_name="es-pe",
        voice_names=voices,
    )

    assert [r.voice for r in results] == voices
    assert service.client.synthesize_speech.call_count == len(voices)


def test_no_real_google_client_created_when_client_preset(service) -> None:
    # El cliente inyectado en la fixture nunca debe ser reemplazado por uno real.
    original_client = service._client
    service.synthesize(text="Hola", profile_name="es-pe")
    assert service._client is original_client
