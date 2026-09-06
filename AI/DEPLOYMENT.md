# Deployment and Operation

## Runtime Model

The production application is one browser-accessible web service:

- FastAPI serves the JSON API.
- FastAPI also serves the compiled React frontend.
- A single backend process runs scheduled Polar synchronization.
- SQLite persists the application data.
- TypeScript is compiled before production startup; no Node service remains running.

Docker is optional. Native and Docker production modes provide the same application functionality and use the same `database/` persistence boundary. See `ARCHITECTURE.md` for the full component, process, and build model.

The portable Docker startup command from the project root one level above this `AI/` directory is:

```bash
docker compose up --build
```

The native production entry point is:

```bash
bash scripts/run.sh
```

A source-only checkout needs Node.js to build the frontend. Once compiled browser assets exist, production runtime needs Python and its dependencies but no continuously running Node process. Run `bash scripts/install-python-runtime-libs.sh` for production-only Python dependencies, or `bash scripts/install-python-libs.sh` for runtime plus development/test dependencies; both target the same cached virtual environment, so run the latter again before development checks. Run `bash scripts/build.sh` to compile assets and `bash scripts/dev.sh` to start FastAPI and Vite for source development.

This project currently resides on a CIFS filesystem mounted `noexec` and without usable symlinks. Invoke repository scripts through `bash`; the scripts place Python environments and frontend dependency/build workspaces under `${XDG_CACHE_HOME:-$HOME/.cache}/polar-web-app/` by default instead of creating executable environments or `node_modules` on the share.

## Persistent Files

All mutable application data is kept under:

```text
database/
├── polar-app.sqlite3
├── backups/
└── logs/                  # optional file logging
```

Docker Compose mounts `./database` into the container. Restarting or rebuilding the container must not remove the database.

SQLite defaults to the `unix-dotfile` VFS and `DELETE` journal mode because POSIX byte-range locking fails on the current CIFS share. This configuration is suitable only for the documented single-process deployment. `POLAR_APP_SQLITE_VFS` and `POLAR_APP_SQLITE_JOURNAL_MODE` may be changed for a host filesystem that safely supports normal SQLite locking and WAL.

`journal_mode` is configured only on an engine's first SQLite connection; it is database-global and must not be reset when later request connections open. If a process is force-killed while using the dotfile VFS, its `database/polar-app.sqlite3.lock/` directory can remain. Stop the process cleanly whenever possible; after confirming no application process is using the database, remove only that stale lock directory before restarting.

Secrets and installation configuration are not application data. They are supplied through environment configuration, excluded from Git, and must never appear in Markdown or logs.

Polar authorization needs `POLAR_APP_POLAR_CLIENT_ID`, `POLAR_APP_POLAR_CLIENT_SECRET`, `POLAR_APP_POLAR_REDIRECT_URI`, and `POLAR_APP_POLAR_TOKEN_ENCRYPTION_KEY`. The exact private setup, token-key lifecycle, native callback URL, Docker variables, and publication checks are in `POLAR_AUTH_SETUP.md`. For the local callback, access the app consistently as `http://localhost:8000`, not by alternating between `localhost` and `127.0.0.1`.

## Scheduled Synchronization

- The sync interval is configurable.
- Scheduling is disabled until Polar authorization succeeds.
- Sync runs cannot overlap.
- Each category records last attempt, last success, duration, and error summary.
- A manual sync endpoint/button remains available.

The initial in-process scheduler assumes exactly one backend worker. Multi-worker or horizontally scaled deployment requires a separate scheduler or distributed locking and is outside the first version.

## Networking

- The default native startup binds to `0.0.0.0` for access from a trusted home LAN. Use `POLAR_APP_HOST=127.0.0.1 bash scripts/run.sh` to restrict it to this computer.
- Keep Polar authorization on the server machine at `http://localhost:8000`: `POLAR_APP_PUBLIC_BASE_URL` and `POLAR_APP_POLAR_REDIRECT_URI` remain unchanged, so LAN binding does not alter Polar OAuth.
- Do not reopen broad public port forwarding for routine use.
- If access beyond the trusted home network is added, require authentication and HTTPS behind a properly configured reverse proxy or VPN.
- If Polar rejects local OAuth callbacks, expose only the callback route temporarily and remove that exposure after authorization.

## Backups

Create a live-database-safe backup with SQLite's online backup API:

```bash
bash scripts/backup-database.sh
```

The command writes `database/backups/polar-app-YYYYMMDDTHHMMSSZ.sqlite3` only after `PRAGMA integrity_check` returns `ok`; a failed copy leaves no completed backup. The backup and database are ignored by Git because they contain personal health data.

To restore a chosen backup, first stop the native or Docker application and confirm no process holds the database. Preserve the current database before replacement, then copy the selected verified backup into place:

```bash
mv database/polar-app.sqlite3 database/polar-app.sqlite3.before-restore
cp database/backups/polar-app-YYYYMMDDTHHMMSSZ.sqlite3 database/polar-app.sqlite3
bash scripts/run.sh
```

After startup, check the health endpoint and expected Timeline/Training data. Do not run a native and Docker process against the same database during backup or restore.

## Upgrade Requirements

- Back up the database before migrations.
- Run Alembic migrations during controlled startup or an explicit upgrade command.
- Preserve raw Polar payloads and normalized source records across upgrades.
- If aggregation formulas, mapping semantics, or timezone change, run the deterministic full aggregate rebuild.

## Native Startup Acceptance

A prepared build on a machine with Python should be able to:

1. Create/activate the documented virtual environment and install Python dependencies.
2. Run `bash scripts/run.sh`.
3. Open the configured URL in a browser without a running Node service.
4. Use the same `database/` directory and application features as Docker mode.
5. Stop cleanly and restart without data loss.

A source-only checkout additionally requires Node.js for `bash scripts/build.sh` or frontend development.

## Portable Docker Startup Acceptance

A clean machine with Docker and Docker Compose should be able to:

1. Clone/copy this directory.
2. Create local environment configuration from `.env.example`.
3. Run `docker compose up --build`.
4. Open the configured URL in a browser.
5. Restart/rebuild the service without losing anything in `database/`.

Current verification status: `docker compose config --quiet` passes. Image build and container startup remain unverified in the current session because the host account cannot access `/var/run/docker.sock` and passwordless sudo is unavailable.
