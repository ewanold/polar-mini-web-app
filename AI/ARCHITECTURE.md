# Application Architecture

## Summary

The Polar web app is primarily a Python application with a React/TypeScript browser interface.

- Python owns data acquisition, OAuth, synchronization, normalization, aggregation, persistence, validation, and the HTTP API.
- React/TypeScript owns the interactive browser interface and chart rendering.
- TypeScript is compiled into static HTML, CSS, and JavaScript before production startup; Python does not interpret TypeScript.
- In production, one FastAPI/Uvicorn service serves both the compiled frontend and the JSON API.
- Docker is a supported packaging and deployment option, not a runtime requirement.

A concise description is:

> A Python/FastAPI data service with a compiled React/TypeScript interface, deployable natively or as one Dockerized web application.

## Component View

```text
┌─────────────────────────────────────────────────────────┐
│ Browser                                                 │
│                                                         │
│ React + TypeScript                                      │
│ - Daily timeline                                        │
│ - Training progress graphs                              │
│ - Training-type mapping                                 │
│ - Manual-entry forms                                    │
│ - Synchronization status                                │
│ - Runtime light/dark theme                              │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/JSON via /api/...
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Python service: FastAPI + Uvicorn                       │
│                                                         │
│ - Serves compiled browser files                         │
│ - Provides JSON API                                     │
│ - Handles Polar OAuth                                   │
│ - Downloads and normalizes Polar data                   │
│ - Maintains rebuildable training aggregate archives             │
│ - Runs scheduled synchronization                        │
│ - Validates and stores manual entries                   │
└────────────────────────┬────────────────────────────────┘
                         │ SQLAlchemy
                         ▼
┌─────────────────────────────────────────────────────────┐
│ SQLite                                                  │
│ database/polar-app.sqlite3                              │
│                                                         │
│ - Raw Polar responses                                   │
│ - Normalized health and training data                   │
│ - Manual entries                                        │
│ - Training-type mappings                                │
│ - Training groups and sport mappings; later daily/weekly/monthly aggregates │
│ - OAuth and synchronization state                       │
└─────────────────────────────────────────────────────────┘
```

Only the Python backend accesses SQLite. The browser obtains and changes data through the HTTP API.

## Backend Responsibilities

The long-running Python service is the core application. It is responsible for:

- Polar OAuth authorization-code flow, encrypted access-token storage, and Polar user registration
- Scheduled and manually triggered Polar synchronization across training, sleep, Nightly Recharge, activity, and continuous heart-rate categories
- Request timeouts, rate-limit handling, retry/backoff, and error reporting
- Storage of raw API payloads
- Normalization into stable domain tables
- User-defined training groups and Polar sport mappings
- User-defined groups, sport mappings, and aggregate-backed training series APIs
- RRD-inspired daily, weekly, and monthly aggregate maintenance
- Manual daily/timed context entries
- JSON API validation and serialization
- Serving the compiled frontend
- Database migrations, health status, and operational diagnostics

Primary backend technologies:

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy 2 and Alembic
- SQLite
- Pydantic Settings
- HTTPX and cryptography/Fernet
- APScheduler

## Frontend Responsibilities

The React/TypeScript frontend runs in the user's browser. It is responsible for:

- Rendering the daily timeline
- Rendering synchronized Apache ECharts training graphs
- Switching daily, weekly, and monthly training ranges
- Training-group and Polar sport-type mapping controls
- Manual-entry forms and client-side validation
- Loading, empty, validation, and error states
- Runtime light/dark theme switching
- Accessible keyboard and screen-reader interaction

The frontend does not access SQLite, store Polar credentials, synchronize Polar data, or calculate authoritative aggregate values. These remain backend responsibilities.

The implemented Settings page calls `GET /api/polar/status`, opens `/api/polar/connect` for the Polar-owned browser authorization flow, and posts to `/api/polar/sync`. It renders category counts returned by the backend; it never receives OAuth secrets or decrypted tokens.

Primary frontend technologies:

- React and TypeScript
- Vite
- Apache ECharts
- TanStack Query
- React Router
- React Hook Form and Zod
- CSS custom properties for themes

## Build Boundary

During development, the frontend consists of TypeScript and React source files. Vite compiles them into ordinary browser assets:

```text
React/TypeScript source
          │
          │ npm run build
          ▼
HTML + CSS + JavaScript
          │
          │ copied into the backend static directory
          ▼
FastAPI serves the files
```

Node.js is required to build or develop the frontend. It is not required as a continuously running production service.

A prepared release may include compiled frontend assets. Such a release can run with only Python and the installed Python dependencies. A source-only checkout requires Node.js once to build the frontend.

## Request and Data Flow

Example training-chart request:

```text
Browser
  │
  │ GET /api/training/groups/1/series?range=6m
  ▼
FastAPI route
  │
  │ validates group and requested range
  ▼
Aggregate-series query
  │
  │ reads materialized aggregate rows
  ▼
SQLAlchemy / SQLite
  │
  │ returns ordered buckets
  ▼
FastAPI JSON response
  │
  ▼
React state (React Query cache is planned)
  │
  ▼
React page renders data/empty state and Apache ECharts synchronized panels
```

Example scheduled synchronization:

```text
APScheduler interval
  │
  ▼
Polar sync coordinator
  ├── refresh OAuth token if needed
  ├── fetch changed Polar records
  ├── retain raw payloads
  ├── normalize and upsert records
  ├── refresh affected aggregate buckets
  └── record sync status
```

## Runtime Modes

### Native production mode

One long-running Python process serves the complete application:

```text
Uvicorn/FastAPI
├── compiled frontend
├── JSON API
├── Polar synchronization scheduler
└── SQLite access
```

The native production entry point is:

```bash
bash scripts/run.sh
```

The script:

1. Verify the Python environment and installed dependencies.
2. Verify that compiled frontend assets exist, or explain how to build them.
3. Create required `database/` subdirectories.
4. Apply Alembic migrations.
5. Start Uvicorn with the configured host and port.

Native production mode retains all application features. It does not lose scheduler, API, UI, aggregation, persistence, or LAN access functionality.

### Native development mode

Development normally uses two processes:

```text
Vite development server       FastAPI/Uvicorn
localhost:5173                localhost:8000
        │                              │
        └──── proxies /api ────────────┘
```

This separation exists for fast frontend rebuilding and diagnostics, not because production requires a Node service. `bash scripts/dev.sh` supervises both development processes.

### Docker production mode

Docker uses a multi-stage image:

1. A Node build stage compiles the frontend.
2. A Python runtime stage receives the compiled assets.
3. The runtime starts one FastAPI/Uvicorn process.
4. Docker Compose mounts `./database` into the container.

```text
One runtime container
├── Python/FastAPI
├── compiled frontend files
└── mounted database/
```

The expected command is:

```bash
docker compose up --build
```

## Native Versus Docker

Docker provides:

- Pinned Python and Node versions
- Reproducible dependency installation and frontend build
- Filesystem and dependency isolation
- A standardized startup command
- Easier movement between machines
- Explicit persistent-directory mounting

Native operation retains all application features but places responsibility for Python, Node during builds, virtual environments, system libraries, startup supervision, and upgrades on the host.

The proposed Docker deployment does not provide meaningful internal process separation because it intentionally runs one application process. Therefore, running natively does not remove process separation that the first Docker design would otherwise provide. The primary difference is environment isolation and repeatability.

## Process Model and Scheduler Constraint

The initial architecture intentionally uses one FastAPI/Uvicorn worker. APScheduler runs inside that process.

Benefits:

- Simple installation
- No message broker
- No separate worker lifecycle
- Suitable for a personal, single-user home server

Constraint:

- Starting multiple Uvicorn workers would start multiple schedulers unless additional coordination were introduced.

The run scripts and Docker configuration must therefore use exactly one worker. Synchronization also uses a database-backed running flag/lock to prevent overlap.

## Possible Future Separation

If scale or reliability later requires it, synchronization can become a separate process:

```text
FastAPI web process ───┐
                       ├── SQLite or PostgreSQL
Sync worker process ───┘
```

That design would require stronger job coordination and careful handling of SQLite write contention, or a move to PostgreSQL. It is intentionally outside the first version because it adds complexity without a current need.

## Persistent Data Boundary

All mutable application data belongs under:

```text
database/
├── polar-app.sqlite3
├── backups/
└── logs/                  # optional file logs
```

Secrets and installation settings are configuration rather than application data. They are supplied through ignored environment configuration and must not be committed or written into Markdown.

Both native and Docker modes use the same `database/` directory and database schema. It should be possible to stop one mode and start the other against the same database after ensuring that only one instance is running.

The current CIFS project filesystem cannot provide the byte-range locking expected by SQLite's default Unix VFS. The application therefore defaults to SQLite's `unix-dotfile` VFS with `DELETE` journaling and exactly one backend process. The settings remain configurable for deployment on a local filesystem that supports normal SQLite locking and WAL.

## Deployment Guidance

- Use Docker Compose when repeatability and easy home-server migration are most important.
- Use native production mode when minimizing Docker overhead or integrating with existing host administration is more important.
- Use `systemd` or another host service manager for unattended native operation, automatic restart, and startup after boot.
- Never run Docker and native instances simultaneously against the same SQLite database.
- Bind to localhost by default; explicitly enable trusted-LAN access when required.

## Architectural Acceptance Criteria

- [x] Production uses one browser URL and one configured service port.
- [x] FastAPI serves both the API and compiled frontend.
- [x] No Node process is required after the frontend has been built.
- [ ] Native and Docker modes provide the same application features.
- [x] Native and Docker configurations use the same `database/` persistence boundary; Docker runtime persistence still needs host-level verification.
- [x] Exactly one backend worker is configured against a database.
- [x] The browser never receives Polar secrets or direct database access in the foundation implementation.
- [x] A prepared release runs without Docker and without a continuously running Node service.
