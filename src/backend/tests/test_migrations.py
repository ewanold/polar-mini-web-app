from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command


def test_initial_migration_upgrades_an_empty_database(tmp_path: Path) -> None:
    database_path = tmp_path / "migration" / "polar.sqlite3"
    alembic_config = Config(Path(__file__).parents[1] / "alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    engine.dispose()

    assert revision == "0008"


def test_migration_uses_application_database_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "configured" / "polar.sqlite3"
    monkeypatch.setenv("POLAR_APP_DATABASE_PATH", str(database_path))
    alembic_config = Config(Path(__file__).parents[1] / "alembic.ini")

    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    engine.dispose()

    assert revision == "0008"


def test_polar_source_data_migration_creates_required_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "migration" / "polar.sqlite3"
    alembic_config = Config(Path(__file__).parents[1] / "alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        tables = set(connection.dialect.get_table_names(connection))
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    engine.dispose()

    assert revision == "0008"
    assert {
        "polar_raw_payloads",
        "polar_training_sessions",
        "polar_sleep_days",
        "polar_nightly_recharge",
        "polar_activity_days",
        "polar_heart_rate_samples",
        "polar_oauth_tokens",
        "polar_sync_state",
        "polar_sport_type_mappings",
        "training_groups",
        "training_aggregates",
        "timeline_events",
    } <= tables
