from pathlib import Path

from sqlalchemy import text

from polar_app.config import Settings
from polar_app.db import create_session_dependency, create_session_factory, create_sqlite_engine


def test_database_parent_is_created(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "polar.sqlite3"
    settings = Settings(database_path=database_path)

    engine = create_sqlite_engine(settings)

    assert database_path.parent.is_dir()
    engine.dispose()


def test_sqlite_connections_enable_foreign_keys_and_configured_journal(
    tmp_path: Path,
) -> None:
    settings = Settings(database_path=tmp_path / "polar.sqlite3")
    engine = create_sqlite_engine(settings)

    with engine.connect() as connection:
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()

    assert foreign_keys == 1
    assert journal_mode == "delete"
    engine.dispose()


def test_second_sqlite_connection_does_not_reconfigure_global_journal_mode(
    tmp_path: Path,
) -> None:
    engine = create_sqlite_engine(Settings(database_path=tmp_path / "polar.sqlite3"))

    with engine.connect() as first_connection, engine.connect() as second_connection:
        assert first_connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "delete"
        assert second_connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

    engine.dispose()


def test_session_dependency_rolls_back_failed_request(tmp_path: Path) -> None:
    settings = Settings(database_path=tmp_path / "polar.sqlite3")
    engine = create_sqlite_engine(settings)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE probe (value INTEGER NOT NULL)"))

    dependency = create_session_dependency(create_session_factory(engine))
    session_iterator = dependency()
    session = next(session_iterator)
    session.execute(text("INSERT INTO probe (value) VALUES (1)"))

    try:
        session_iterator.throw(RuntimeError("request failed"))
    except RuntimeError:
        pass

    with engine.connect() as connection:
        row_count = connection.execute(text("SELECT COUNT(*) FROM probe")).scalar_one()

    assert row_count == 0
    engine.dispose()
