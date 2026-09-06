# Polar Web App

## Goal

Build a private, self-hosted web application for comparing Polar sleep, recovery, activity, and training data with manually entered context such as meals, caffeine, alcohol, medication, stress, illness, mood, subjective sleep quality, and notes.

The application is for personal observation and progress tracking, not medical diagnosis.

## Core Experience

The application has two primary views:

1. **Daily timeline** — a compact, scrollable day-by-day comparison of sleep, recovery, activity, training, meals, and notes.
2. **Training progress** — synchronized graphs for user-defined training groups such as Running or Walking, with daily, weekly, and monthly aggregation modes.

Polar sport types are assigned many-to-one to user-defined groups. For example, Polar types such as jogging and trail running can both contribute to the Running group. Types can also remain unmapped or be ignored.

## Architecture

```text
Polar AccessLink OAuth and scheduled sync
                    |
                    v
FastAPI web service + React user interface
                    |
                    v
                 SQLite
                    |
                    v
              database/
```

Selected stack: FastAPI, SQLAlchemy, SQLite, React/TypeScript, Vite, Apache ECharts, and Docker Compose.

Python is the long-running application runtime. TypeScript is compiled into static browser files; it is not interpreted by Python and does not require a continuously running Node service in production. The application can run natively from the command line or through Docker Compose with the same functionality. See `ARCHITECTURE.md` for the component, build, process, and runtime models.

The production build is one browser-accessible web service. It should start reproducibly from the project root one level above this `AI/` directory, run later on a home server, synchronize Polar data at configurable intervals, and keep all mutable application data under `database/`.

## Durable Decisions

- Use the official Polar AccessLink API; do not scrape Polar Flow.
- Use OAuth tokens; never store the Polar account password.
- Retain raw Polar responses together with normalized fields.
- Use SQLite for the initial single-user application.
- Use SQLite dotfile locking with rollback journaling by default because the current project storage is a CIFS share; keep the VFS and journal mode configurable for other hosts.
- Keep normalized sessions indefinitely. The first Training Progress slice calculates mapped-session daily series directly; rebuildable daily, weekly, and monthly aggregate archives remain the next scalability step.
- Use arithmetic means of session values to track changes in a typical session rather than total training volume.
- Provide runtime light and dark themes.
- Keep the service private by default; do not expose it publicly without authentication and HTTPS.

## Documentation Map

- `IMPLEMENTATION_PLAN.md` — detailed architecture, selected libraries, ordered implementation tasks, tests, risks, and definition of done.
- `ARCHITECTURE.md` — Python/TypeScript responsibilities, build boundary, request flow, native/Docker runtime modes, and process model.
- `POLAR_API.md` — OAuth, API versions, data categories, scopes, rate limits, and research questions.
- `POLAR_AUTH_SETUP.md` — private OAuth client setup, Fernet token encryption, local callback behavior, synchronization, troubleshooting, Docker variables, and GitHub publication checks.
- `DATA_MODEL.md` — persistence, schema outline, raw payloads, mapping, and aggregate rules.
- `UI.md` — daily timeline, training charts, mapping interface, visual references, and themes.
- `DEPLOYMENT.md` — startup, storage, scheduler, networking, backups, and security.
- `TODOS.md` — concise current work queue.
- `LOG.md` — dated decisions and meaningful milestones.
- `LINKS.md` — primary external references and library links.
- `DOCUMENTATION.md` — documentation responsibilities and maintenance rules.

The Markdown files in this directory are the durable project knowledge base. Keep this file lean and move implementation or research detail into the focused documents above.
