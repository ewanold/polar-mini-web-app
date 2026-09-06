from pathlib import Path

import pytest
from pydantic import ValidationError

from polar_app.config import PROJECT_ROOT, Settings


def test_settings_have_portable_validated_defaults() -> None:
    settings = Settings(_env_file=None)

    project_root = Path(__file__).parents[3]
    assert settings.database_path == project_root / "database/polar-app.sqlite3"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.timezone == "Europe/Berlin"
    assert settings.sync_interval_minutes == 60
    assert settings.public_base_url == "http://localhost:8000"
    assert settings.sqlite_vfs == "unix-dotfile"
    assert settings.sqlite_journal_mode == "DELETE"


def test_settings_load_polar_app_environment_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("POLAR_APP_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("POLAR_APP_HOST", "0.0.0.0")
    monkeypatch.setenv("POLAR_APP_PORT", "9000")
    monkeypatch.setenv("POLAR_APP_TIMEZONE", "America/New_York")
    monkeypatch.setenv("POLAR_APP_SYNC_INTERVAL_MINUTES", "15")
    monkeypatch.setenv("POLAR_APP_PUBLIC_BASE_URL", "https://polar.home.example")
    monkeypatch.setenv("POLAR_APP_SQLITE_VFS", "")
    monkeypatch.setenv("POLAR_APP_SQLITE_JOURNAL_MODE", "WAL")

    settings = Settings()

    assert settings.database_path == database_path
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.timezone == "America/New_York"
    assert settings.sync_interval_minutes == 15
    assert settings.sqlite_vfs is None
    assert settings.sqlite_journal_mode == "WAL"


def test_settings_load_polar_oauth_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLAR_APP_POLAR_CLIENT_ID", "client-id")
    monkeypatch.setenv("POLAR_APP_POLAR_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("POLAR_APP_POLAR_REDIRECT_URI", "http://localhost:8000/api/polar/callback")

    settings = Settings()

    assert settings.polar_client_id == "client-id"
    assert settings.polar_client_secret.get_secret_value() == "client-secret"
    assert settings.polar_redirect_uri == "http://localhost:8000/api/polar/callback"


def test_sync_interval_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(sync_interval_minutes=0)


def test_public_base_url_must_be_http_or_https() -> None:
    with pytest.raises(ValidationError):
        Settings(public_base_url="ftp://polar.example")


def test_environment_file_is_resolved_from_project_root() -> None:
    assert PROJECT_ROOT == Path(__file__).parents[3]
    assert Settings.model_config["env_file"] == PROJECT_ROOT / ".env"
