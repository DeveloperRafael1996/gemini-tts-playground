"""Perfiles de idioma/acento y lista centralizada de voces disponibles."""

from google_tts_demo.exceptions import TTSProfileNotFoundError
from google_tts_demo.models import TTSProfile

# Lista centralizada de voces Gemini TTS. Ampliable en un unico lugar
# para que CLI y Playground nunca dupliquen esta informacion.
AVAILABLE_VOICES: list[str] = [
    "Kore",
    "Aoede",
    "Leda",
    "Charon",
    "Puck",
    "Fenrir",
    "Zephyr",
    "Achernar",
    "Schedar",
    "Sulafat",
]

# Genero perceptual de cada voz Gemini TTS, segun la documentacion oficial
# (ai.google.dev/gemini-api/docs/speech-generation). Permite agrupar/filtrar
# las voces por genero en la UI.
VOICE_GENDERS: dict[str, str] = {
    "Kore": "Female",
    "Aoede": "Female",
    "Leda": "Female",
    "Zephyr": "Female",
    "Achernar": "Female",
    "Sulafat": "Female",
    "Charon": "Male",
    "Puck": "Male",
    "Fenrir": "Male",
    "Schedar": "Male",
}

DEFAULT_VOICE = "Kore"


def voice_gender(voice_name: str) -> str:
    """Retorna el genero perceptual de una voz ('Female'/'Male'/'Unknown')."""
    return VOICE_GENDERS.get(voice_name, "Unknown")

PROFILES: dict[str, TTSProfile] = {
    "es-latam": TTSProfile(
        name="es-latam",
        display_name="Español Latinoamérica",
        language_code="es-419",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Habla en español latinoamericano neutral.\n"
            "Usa una voz profesional, cálida y natural.\n"
            "Mantén una pronunciación clara y un ritmo moderado."
        ),
    ),
    "es-pe": TTSProfile(
        name="es-pe",
        display_name="Español Perú",
        language_code="es-419",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Habla en español latinoamericano con un acento peruano neutral.\n"
            "Utiliza una pronunciación clara, natural y profesional.\n"
            "Evita regionalismos exagerados.\n"
            "Mantén un tono amable y confiable."
        ),
    ),
    "es-mx": TTSProfile(
        name="es-mx",
        display_name="Español México",
        language_code="es-MX",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Habla en español mexicano neutral.\n"
            "Usa una voz profesional, cercana y natural.\n"
            "Mantén un ritmo moderado y pronunciación clara."
        ),
    ),
    "es-co": TTSProfile(
        name="es-co",
        display_name="Español Colombia",
        language_code="es-419",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Habla en español latinoamericano con un acento colombiano neutral.\n"
            "Utiliza una voz cálida, profesional y conversacional.\n"
            "Evita exagerar características regionales."
        ),
    ),
    "es-ar": TTSProfile(
        name="es-ar",
        display_name="Español Argentina",
        language_code="es-419",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Habla en español latinoamericano con un acento argentino moderado.\n"
            "Mantén una voz profesional y clara.\n"
            "Evita exagerar características regionales."
        ),
    ),
    "pt-br": TTSProfile(
        name="pt-br",
        display_name="Português Brasil",
        language_code="pt-BR",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Fale em português brasileiro com sotaque brasileiro neutro.\n"
            "Use uma voz profissional, acolhedora e natural.\n"
            "Mantenha um ritmo moderado e uma pronúncia clara."
        ),
    ),
    "pt-br-sp": TTSProfile(
        name="pt-br-sp",
        display_name="Português São Paulo",
        language_code="pt-BR",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Fale em português brasileiro com um leve sotaque de São Paulo.\n"
            "Não exagere o sotaque.\n"
            "Mantenha uma voz profissional e natural."
        ),
    ),
    "pt-br-rio": TTSProfile(
        name="pt-br-rio",
        display_name="Português Rio de Janeiro",
        language_code="pt-BR",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Fale em português brasileiro com um leve sotaque do Rio de Janeiro.\n"
            "Mantenha uma pronúncia clara e profissional.\n"
            "Não exagere características regionais."
        ),
    ),
    "en-us": TTSProfile(
        name="en-us",
        display_name="English US",
        language_code="en-US",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Speak in neutral American English.\n"
            "Use a warm, professional and trustworthy voice.\n"
            "Speak clearly at a moderate pace."
        ),
    ),
    "en-uk": TTSProfile(
        name="en-uk",
        display_name="English UK",
        language_code="en-GB",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Speak natural British English with a neutral professional accent.\n"
            "Use a calm and trustworthy tone."
        ),
    ),
    "en-latam": TTSProfile(
        name="en-latam",
        display_name="English Latin Accent",
        language_code="en-US",
        voice_name=DEFAULT_VOICE,
        prompt=(
            "Speak fluent American English with a subtle Latin American accent.\n"
            "The accent should be natural and light.\n"
            "Maintain clear pronunciation and a professional tone."
        ),
    ),
}


def get_profile(profile_name: str) -> TTSProfile:
    """Obtiene un perfil por su nombre.

    Lanza TTSProfileNotFoundError si el perfil no existe.
    """
    profile = PROFILES.get(profile_name)
    if profile is None:
        raise TTSProfileNotFoundError(f"Perfil no encontrado: {profile_name}")
    return profile


def list_profiles() -> list[TTSProfile]:
    """Retorna todos los perfiles disponibles."""
    return list(PROFILES.values())
