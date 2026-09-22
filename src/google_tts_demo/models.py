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


class TTSCost(BaseModel):
    """Costo estimado (USD) de una sintesis de audio con Gemini TTS."""

    model: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


class TTSResult(BaseModel):
    """Resultado de una sintesis de audio."""

    profile: str
    voice: str
    language_code: str
    output_path: str
    duration_seconds: float
    audio_duration_seconds: float
    cost: TTSCost
