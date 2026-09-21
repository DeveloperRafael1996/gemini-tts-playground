"""Configuracion de la aplicacion basada en variables de entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion cargada desde variables de entorno o un archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_cloud_project: str = ""
    tts_model: str = "gemini-2.5-flash-tts"
    tts_default_voice: str = "Kore"
    tts_output_dir: Path = Path("outputs")
    playground_host: str = "127.0.0.1"
    playground_port: int = 7860

    def ensure_output_dir(self) -> Path:
        """Crea el directorio de salida si no existe y lo retorna."""
        self.tts_output_dir.mkdir(parents=True, exist_ok=True)
        return self.tts_output_dir


settings = Settings()
