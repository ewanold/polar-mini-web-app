from logging.config import fileConfig
from os import environ
from pathlib import Path

from sqlalchemy import engine_from_config, make_url, pool

from alembic import context
from polar_app.config import Settings
from polar_app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    if environ.get("POLAR_APP_DATABASE_PATH"):
        settings = Settings()
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        return settings.database_url
    return config.get_main_option("sqlalchemy.url")


def ensure_database_parent(url: str) -> None:
    database = make_url(url).database
    if database and database != ":memory:":
        Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def run_migrations_offline() -> None:
    url = database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = database_url()
    ensure_database_parent(url)
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
