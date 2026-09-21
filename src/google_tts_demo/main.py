"""CLI para generar audio con Google Cloud Text-to-Speech (Gemini TTS)."""

import argparse
import logging
import sys

from google_tts_demo.exceptions import TTSException
from google_tts_demo.profiles import list_profiles
from google_tts_demo.tts_service import GoogleTTSService

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="google_tts_demo.main",
        description="Genera audio con Google Cloud Text-to-Speech usando Gemini TTS.",
    )
    parser.add_argument("--profile", help="Nombre del perfil de idioma/acento (ej: es-pe)")
    parser.add_argument("--text", help="Texto a sintetizar")
    parser.add_argument("--output", help="Nombre de archivo de salida (opcional)")
    parser.add_argument("--voice", help="Nombre de voz a utilizar (opcional)")
    parser.add_argument(
        "--voices",
        help="Lista de voces separadas por coma para comparacion A/B (ej: Kore,Aoede,Leda)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="Lista todos los perfiles disponibles y termina",
    )
    return parser


def _print_profiles() -> None:
    for profile in list_profiles():
        print(f"{profile.name}\t{profile.display_name}\t{profile.language_code}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles:
        _print_profiles()
        return 0

    if not args.profile or not args.text:
        parser.error("--profile y --text son obligatorios (o utiliza --list-profiles)")

    service = GoogleTTSService()

    try:
        if args.voices:
            voice_names = [v.strip() for v in args.voices.split(",") if v.strip()]
            results = service.synthesize_many(
                text=args.text,
                profile_name=args.profile,
                voice_names=voice_names,
            )
            for result in results:
                print(f"Generado: {result.output_path} (voice={result.voice})")
        else:
            result = service.synthesize(
                text=args.text,
                profile_name=args.profile,
                output_filename=args.output,
                voice_name=args.voice,
            )
            print(f"Generado: {result.output_path}")
    except TTSException as exc:
        logger.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
