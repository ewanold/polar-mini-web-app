# Current Todos

The complete ordered implementation checklist is in `IMPLEMENTATION_PLAN.md`. This file is the concise current work queue and should change as work progresses.

## Completed Foundation

- [x] Create the FastAPI package, validated configuration, and tested health endpoint.
- [x] Create the React/TypeScript/Vite application shell and primary routes.
- [x] Add Docker Compose, multi-stage image build, native production build/run scripts, native development supervision, `.env.example`, and Git exclusions.
- [x] Verify native production and development startup through `bash scripts/run.sh` and `bash scripts/dev.sh`.
- [x] Configure SQLite, SQLAlchemy, foreign keys, CIFS-compatible dotfile locking/rollback journaling, and Alembic migrations.
- [ ] Run `docker compose up --build` and verify restart/persistence on a host account with Docker-daemon access. Compose configuration is validated, but this account is not in the `docker` group.
- [ ] Verify Docker and native modes use and preserve the same data under `database/` after Docker runtime verification becomes available.

## Completed: Polar API and Source Data

- [x] Verify and document the implemented AccessLink v3 OAuth flow, scope, endpoints, data windows, units, and rate-limit behavior.
- [x] Model raw Polar payloads, normalized source records, encrypted OAuth token metadata, sync state, and training groups/sport mappings; migrate schema through revision `0004`.
- [x] Implement and test OAuth connect/callback, anti-CSRF state, encrypted token persistence, Polar user registration, connection status, and disconnect APIs.
- [x] Implement the resilient authenticated client and idempotent training, sleep, Nightly Recharge, activity, and continuous-heart-rate synchronization.
- [x] Add manual `POST /api/polar/sync` and configurable, non-overlapping in-process scheduled synchronization.
- [x] Verify native startup configures the non-overlapping Polar re-sync scheduler at the default 60-minute interval. Observe a full unattended production cycle during deployment validation.
- [x] Add the Settings connection state, Connect Polar action, Sync now control, and new/updated/unchanged/error result display.
- [x] Verify a real local OAuth connection and initial activity import. See `POLAR_AUTH_SETUP.md` for safe configuration and GitHub publication checks.

## Current Next Phase: Training Progress

- [x] Implement collected training groups and many-to-one Polar sport mapping persistence.
- [x] Implement group create/list, observed-sport-type list, atomic mapping update, and chart-ready series APIs.
- [x] Implement browser-visible group creation/listing and Training Progress range/empty-data states.
- [x] Implement direct daily aggregation of mapped sessions for the initial series endpoint.
- [x] Extend the Mapping page to display observed sport types, their counts/statuses, and assignment controls.
- [x] Add training-group deletion with confirmation and required reassignment or unmapping of mapped Polar sport types.
- [x] Implement deterministic day/week/month bucket boundaries and local-time conversion.
- [x] Calculate and store metric-specific sample counts in aggregate archives.
- [x] Implement incremental and full aggregate rebuilds, including a recovery CLI.
- [x] Expose aggregate archives through range-specific continuous chart-series buckets, including empty buckets and metric metadata.
- [x] Build synchronized Training Progress charts for total distance, mean heart rate, mean pace, mean duration, and duration/pace index.
- [x] Add a selected-group control and persist the selected range in the URL.
- [x] Add contributing-session drill-down.
- [x] Diagnose and fix the Training Progress chart pointer so it tracks across populated and empty buckets.
- [x] Complete translation coverage for Training, Mappings, Settings, theme controls, chart labels, validation, and status messages in English, German, and Russian.

## Timeline and Completion

- [x] Build the Polar-backed daily Timeline: nightly-recovery tiles, a rolling 24-hour continuous-heart-rate chart, and 28-day nightly metric charts.
- [ ] Add manual-context forms and incorporate their entries into the Timeline.
- [x] Add dated free-text Timeline events through chart right-click, with highlighted chart markers and hover details.
- [x] Add the runtime light/dark theme foundation with local persistence.
- [x] Add a UI language selector with persisted language preference and translated application text in English, German, and Russian.
- [ ] Add backups, operational documentation, end-to-end tests, and security review.
- [ ] Complete the release verification checklist in `IMPLEMENTATION_PLAN.md`.

## Documentation Discipline

- [x] Review and synchronize every visible Markdown file in this directory for the 2026-09-03 Training Progress checkpoint.
- [ ] Keep `MAIN.md` concise; put detailed research and implementation knowledge in focused documents.
