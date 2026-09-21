"""Modelos Pydantic del dominio TTS."""

from pydantic import BaseModel


class TTSProfile(BaseModel):
    """Perfil de idioma/acento/estilo utilizado para generar audio."""

    name: str
    display_name: str
    language_code: str
    voice_name: str
    prompt: str


class TTSRequest(BaseModel):
    """Solicitud de sintesis de audio."""

    text: str
    profile_name: str
    voice_name: str | None = None
    custom_prompt: str | None = None


class TTSResult(BaseModel):
    """Resultado de una sintesis de audio."""

    profile: str
    voice: str
    language_code: str
    output_path: str
    duration_seconds: float
