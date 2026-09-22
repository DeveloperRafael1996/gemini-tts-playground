"""Calculo del costo estimado de generacion de audio con Gemini TTS.

Precios oficiales de Google Cloud Text-to-Speech (Gemini-TTS), consultados el
2026-09-21 en https://cloud.google.com/text-to-speech/pricing. Los tokens de
audio de salida equivalen a 25 tokens por segundo de audio generado (dato
publicado en la misma pagina). Los tokens de texto de entrada no son
devueltos por la API, por lo que se estiman con la aproximacion estandar de
Gemini de ~4 caracteres por token.
"""

import math

from google_tts_demo.models import TTSCost

# model_name -> (precio USD por 1M tokens de entrada, precio USD por 1M tokens de salida)
GEMINI_TTS_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash-tts": (0.50, 10.00),
    "gemini-2.5-flash-lite-preview-tts": (0.50, 10.00),
    "gemini-2.5-pro-tts": (1.00, 20.00),
    "gemini-3.1-flash-tts-preview": (1.00, 20.00),
}
_DEFAULT_MODEL = "gemini-2.5-flash-tts"

AVAILABLE_MODELS = list(GEMINI_TTS_PRICING.keys())

AUDIO_TOKENS_PER_SECOND = 25
CHARACTERS_PER_TOKEN_ESTIMATE = 4.0


def estimate_input_tokens(text: str) -> int:
    """Estima los tokens de texto de entrada (~4 caracteres por token)."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / CHARACTERS_PER_TOKEN_ESTIMATE))


def estimate_output_tokens(audio_duration_seconds: float) -> int:
    """Estima los tokens de audio de salida (25 tokens por segundo de audio)."""
    if audio_duration_seconds <= 0:
        return 0
    return round(audio_duration_seconds * AUDIO_TOKENS_PER_SECOND)


def calculate_cost(text: str, audio_duration_seconds: float, model_name: str) -> TTSCost:
    """Calcula el costo estimado (USD) de una sintesis de audio con Gemini TTS.

    Si el modelo no esta en la tabla de precios conocida, se usa la tarifa de
    gemini-2.5-flash-tts como aproximacion razonable.
    """
    input_price_per_million, output_price_per_million = GEMINI_TTS_PRICING.get(
        model_name, GEMINI_TTS_PRICING[_DEFAULT_MODEL]
    )

    input_tokens = estimate_input_tokens(text)
    output_tokens = estimate_output_tokens(audio_duration_seconds)

    input_cost_usd = (input_tokens / 1_000_000) * input_price_per_million
    output_cost_usd = (output_tokens / 1_000_000) * output_price_per_million

    return TTSCost(
        model=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=input_cost_usd,
        output_cost_usd=output_cost_usd,
        total_cost_usd=input_cost_usd + output_cost_usd,
    )
