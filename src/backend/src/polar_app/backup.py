"""Create integrity-checked SQLite backups without copying a live database file."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from polar_app.config import Settings


def _sqlite_uri(path: Path, *, vfs: str | None, read_only: bool) -> str | Path:
    if vfs is None:
        return path
    mode = "ro" if read_only else "rwc"
    return f"file:{quote(path.resolve().as_posix(), safe='/')}?mode={mode}&vfs={quote(vfs)}"


def _connect(path: Path, *, vfs: str | None, read_only: bool) -> sqlite3.Connection:
    database = _sqlite_uri(path, vfs=vfs, read_only=read_only)
    return sqlite3.connect(database, uri=isinstance(database, str))


def create_backup(
    source: Path,
    backup_dir: Path,
    *,
    now: datetime | None = None,
    sqlite_vfs: str | None = None,
) -> Path:
    """Back up ``source`` online, verify it, then publish the finished file."""
    if not source.is_file():
        raise FileNotFoundError(f"SQLite database does not exist: {source}")

    timestamp = (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"{source.stem}-{timestamp}.sqlite3"
    partial = destination.with_suffix(".sqlite3.partial")
    if destination.exists() or partial.exists():
        raise FileExistsError(f"Backup path already exists: {destination}")

    try:
        with _connect(source, vfs=sqlite_vfs, read_only=True) as source_connection:
            with _connect(partial, vfs=sqlite_vfs, read_only=False) as destination_connection:
                source_connection.backup(destination_connection)
                integrity = destination_connection.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return destination


def main() -> None:
    settings = Settings()
    parser = argparse.ArgumentParser(description="Create an integrity-checked SQLite backup.")
    parser.add_argument("--database", type=Path, default=settings.database_path)
    parser.add_argument("--output-dir", type=Path, default=None)
    arguments = parser.parse_args()
    output_dir = arguments.output_dir or arguments.database.parent / "backups"
    backup = create_backup(
        arguments.database,
        output_dir,
        sqlite_vfs=settings.sqlite_vfs,
    )
    print(backup)


if __name__ == "__main__":
    main()
