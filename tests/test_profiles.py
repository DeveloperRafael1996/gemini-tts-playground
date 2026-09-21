"""Tests para el registro centralizado de perfiles TTS."""

import pytest

from google_tts_demo.exceptions import TTSProfileNotFoundError
from google_tts_demo.models import TTSProfile
from google_tts_demo.profiles import AVAILABLE_VOICES, get_profile, list_profiles


def test_get_profile_existing_returns_profile() -> None:
    profile = get_profile("es-pe")

    assert isinstance(profile, TTSProfile)
    assert profile.name == "es-pe"
    assert profile.language_code == "es-419"
    assert "peruano" in profile.prompt.lower()


def test_get_profile_unknown_raises_not_found_error() -> None:
    with pytest.raises(TTSProfileNotFoundError):
        get_profile("does-not-exist")


def test_list_profiles_contains_expected_profiles() -> None:
    names = {profile.name for profile in list_profiles()}

    expected = {
        "es-latam",
        "es-pe",
        "es-mx",
        "es-co",
        "es-ar",
        "pt-br",
        "pt-br-sp",
        "pt-br-rio",
        "en-us",
        "en-uk",
        "en-latam",
    }
    assert expected.issubset(names)


def test_available_voices_are_centralized_and_non_empty() -> None:
    assert len(AVAILABLE_VOICES) > 0
    assert "Kore" in AVAILABLE_VOICES
    assert len(AVAILABLE_VOICES) == len(set(AVAILABLE_VOICES))
