import sqlite3
from datetime import UTC, datetime

from polar_app.backup import create_backup


def test_create_backup_copies_database_and_checks_integrity(tmp_path) -> None:
    source = tmp_path / "polar.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
        connection.execute("INSERT INTO notes (text) VALUES ('protected local data')")

    backup = create_backup(
        source,
        tmp_path / "backups",
        now=datetime(2026, 9, 6, 12, 30, tzinfo=UTC),
    )

    assert backup == tmp_path / "backups" / "polar-20260906T123000Z.sqlite3"
    with sqlite3.connect(backup) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("SELECT text FROM notes").fetchone() == (
            "protected local data",
        )
