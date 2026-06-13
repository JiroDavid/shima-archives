import pytest

from app.core.config import Settings


def test_cors_origins_parses_comma_separated_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://example.com")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["http://localhost:3000", "http://example.com"]


def test_cors_origins_defaults_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["http://localhost:3000"]
