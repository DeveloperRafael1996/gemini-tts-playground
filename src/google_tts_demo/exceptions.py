"""Excepciones del dominio TTS."""


class TTSException(Exception):
    """Excepcion base para errores relacionados con TTS."""


class TTSProfileNotFoundError(TTSException):
    """Se lanza cuando no existe un perfil con el nombre solicitado."""


class TTSSynthesisError(TTSException):
    """Se lanza cuando falla la sintesis de audio en Google Cloud TTS."""
