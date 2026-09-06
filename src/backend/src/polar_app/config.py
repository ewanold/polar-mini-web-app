from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "database" / "polar-app.sqlite3"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POLAR_APP_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
        validate_default=True,
    )

    database_path: Path = DEFAULT_DATABASE_PATH
    host: str = "127.0.0.1"
    port: Annotated[int, Field(ge=1, le=65535)] = 8000
    timezone: str = "Europe/Berlin"
    sync_interval_minutes: Annotated[int, Field(gt=0)] = 60
    public_base_url: str = "http://localhost:8000"
    sqlite_vfs: Literal["unix-dotfile"] | None = "unix-dotfile"
    sqlite_journal_mode: Literal["DELETE", "WAL"] = "DELETE"
    polar_client_id: str | None = None
    polar_client_secret: SecretStr | None = None
    polar_redirect_uri: str = "http://localhost:8000/api/polar/callback"
    polar_token_encryption_key: SecretStr | None = None

    @field_validator("sqlite_vfs", mode="before")
    @classmethod
    def empty_vfs_means_default_sqlite_vfs(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("public_base_url")
    @classmethod
    def public_base_url_must_be_http(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("public base URL must be an absolute HTTP(S) URL")
        return value.rstrip("/")

    @field_validator("polar_redirect_uri")
    @classmethod
    def polar_redirect_uri_must_be_http(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Polar redirect URI must be an absolute HTTP(S) URL")
        return value

    @property
    def database_url(self) -> str:
        path = self.database_path.expanduser().resolve()
        if self.sqlite_vfs:
            return f"sqlite+pysqlite:///file:{path}?vfs={self.sqlite_vfs}&uri=true"
        return f"sqlite+pysqlite:///{path}"

    @field_validator("timezone")
    @classmethod
    def timezone_must_exist(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"unknown timezone: {value}") from error
        return value
