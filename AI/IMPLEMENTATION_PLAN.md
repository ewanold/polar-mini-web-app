# Polar Web App Implementation Plan

> **For Hermes:** Implement this plan task-by-task. Use test-driven development for aggregation, mapping, synchronization, and API behavior. Verify each phase before continuing.

**Goal:** Build a portable, self-hosted web service that imports Polar training, sleep, recovery, and activity data; stores all mutable application data under `database/`; supports manual daily context; and provides timeline and accumulated training-progress views with runtime light/dark themes.

**Architecture:** Use a FastAPI backend and SQLite database, with a React/TypeScript frontend built by Vite. Python is the long-running runtime; TypeScript is compiled into static HTML, CSS, and JavaScript before production startup. FastAPI serves both the JSON API and compiled frontend so the application runs as one web service. Native command-line and Docker deployments provide the same features; Docker supplies build/environment isolation rather than additional application process separation. Polar synchronization runs on a configurable interval in the single backend process. Raw Polar payloads are retained, normalized sessions remain the source of truth, and daily/weekly/monthly training aggregates are materialized as rebuildable caches. See `ARCHITECTURE.md` for the detailed component and runtime model.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, SQLite, Pydantic Settings, HTTPX, cryptography/Fernet, APScheduler, React 19, TypeScript, Vite, React Router, pytest, Vitest, React Testing Library, Ruff, mypy, Docker Compose. Planned future UI/chart libraries remain subject to implementation-time validation.

---

## 1. Confirmed Product Decisions

- [x] The application is a local/self-hosted browser application, not a desktop executable.
- [x] The production application is one web service that can be started from the repository directory.
- [x] Python/FastAPI is the long-running runtime; TypeScript is compiled into browser assets and does not require a production Node service.
- [x] Docker is optional: native and Docker production modes provide the same features and use the same `database/` directory.
- [x] The primary portable startup path is `docker compose up --build`.
- [x] A native production `scripts/run.sh` path will support prepared builds using Python only.
- [x] A native `scripts/dev.sh` path will run Python and Node development processes.
- [x] All mutable application data is kept under `database/`.
- [x] SQLite is the initial database.
- [x] Polar AccessLink is the data source; Polar Flow will not be scraped.
- [x] Raw Polar responses are retained alongside normalized records.
- [x] Polar sport types can be mapped many-to-one into user-defined collected training groups.
- [x] A Polar type can also be marked ignored or left unmapped.
- [x] Unknown Polar types appear in an explicit default/unmapped group until reviewed.
- [x] Training charts use three display modes:
  - Recent 4 weeks: daily buckets for the last 28 calendar days.
  - Past 6 months: calendar-week buckets for the last 26 weeks.
  - All history: calendar-month buckets for all available history.
- [x] Multiple sessions in a bucket use arithmetic means, because the charts are intended to show changes in a typical session rather than total training volume.
- [x] The training metrics are:
  - Mean session heart rate.
  - Mean session pace, displayed as `min/km`.
  - Mean session duration in minutes.
  - Mean per-session `duration / pace` index, calculated as `duration_minutes / pace_minutes_per_km` and displayed without a unit, as requested.
- [x] The theme can be switched between light and dark at runtime.

### Explicit aggregation rule

For every training group and time bucket:

1. Select normalized sessions whose local start date falls in the bucket.
2. Exclude ignored and unmapped sessions from group charts, but expose their counts in the mapping UI.
3. Calculate each session's `duration_pace_index` before aggregation.
4. Calculate an arithmetic mean independently for each non-null metric.
5. Do not substitute zero for missing values.
6. Record a separate sample count for every metric so tooltips can explain how many sessions contributed.
7. Keep session count as metadata/tooltips; do not use total duration as the principal trend metric.
8. Rebuild every resolution directly from normalized sessions rather than averaging lower-resolution averages. This prevents an average-of-averages bias.

### RRD-inspired behavior

The design borrows RRD's fixed-resolution archives without discarding source data:

- Raw and normalized sessions are retained indefinitely.
- Daily, weekly, and monthly aggregate tables act as materialized caches.
- New or changed sessions invalidate and rebuild affected buckets.
- A full rebuild command can reproduce all aggregate rows from normalized sessions.
- The UI requests only the resolution needed by the active range button.

---

## 2. Intended Libraries and Why

### Backend/runtime

| Library | Purpose | Reason |
|---|---|---|
| `fastapi` | HTTP API, OAuth callbacks, static frontend serving | Typed, compact, and well suited to a local data service |
| `uvicorn` | ASGI server | Standard FastAPI production runtime |
| `sqlalchemy>=2` | Database models and queries | Clear transactions and migration support |
| `alembic` | Schema migrations | Makes upgrades safe on the home server |
| SQLite (`sqlite3`) | Persistent storage | Sufficient for a single-user service and easy to back up |
| `pydantic-settings` | Environment/config loading | Validated config without committing secrets |
| `httpx` | Polar API requests | Async HTTP, timeouts, and testable transports |
| `authlib` | OAuth authorization-code flow helpers | Correct state/token handling rather than custom OAuth code |
| `apscheduler` | Periodic Polar synchronization | Configurable in-process interval scheduler for a single worker |
| `tenacity` | Bounded retry/backoff | Handles transient Polar/API failures without tight retry loops |
| Python `zoneinfo` | Local date and bucket boundaries | Avoids another timezone dependency |
| `structlog` | Structured application/sync logs | Useful for unattended home-server operation |

### Frontend

| Library | Purpose | Reason |
|---|---|---|
| `react` + `typescript` | UI | Component model and type-safe frontend |
| `vite` | Development/build tooling | Fast local startup and simple production bundle |
| `react-router-dom` | Timeline, training, mapping, settings routes | Keeps major views addressable |
| `@tanstack/react-query` | API state, caching, refresh status | Avoids hand-written request state |
| `echarts` + `echarts-for-react` | Synchronized training charts | Strong time-series support, zoom, tooltips, linked axes, theme support |
| `react-hook-form` | Mapping/manual-entry forms | Efficient form state |
| `zod` | Client-side validation | Type-compatible validation at API boundaries |
| `date-fns` | Date formatting and range labels | Small, explicit date utilities |
| CSS custom properties | Runtime light/dark theme | No large component framework required; easy chart/theme integration |

### Tests and quality

| Library/tool | Purpose |
|---|---|
| `pytest`, `pytest-asyncio` | Backend unit/integration tests |
| `respx` | Deterministic HTTPX/Polar API tests |
| `time-machine` | Frozen-time tests for daily/weekly/monthly boundaries and DST |
| `vitest` | Frontend unit tests |
| `@testing-library/react` | Component behavior tests |
| `msw` | Browser-like API mocks for frontend tests |
| `playwright` | End-to-end browser tests, including themes and chart controls |
| `ruff` | Python linting and formatting |
| `mypy` | Python type checks |
| `eslint` + `prettier` | TypeScript/CSS quality and formatting |

### Deployment

| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Reproducible startup from the repository on Linux, macOS, or Windows |
| Multi-stage Dockerfile | Builds React assets, then runs one lean FastAPI service |

---

## 3. Proposed Repository Layout

```text
polar-web-app/
├── src/
│   ├── backend/
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   ├── src/polar_app/
│   │   └── tests/
│   └── frontend/
│       ├── package.json
│       ├── vite.config.ts
│       ├── src/
│       └── tests-e2e/
├── database/
│   ├── .gitkeep
│   ├── polar-app.sqlite3        # ignored
│   ├── backups/                 # ignored except documentation
│   └── logs/                    # optional, ignored
├── scripts/
│   ├── build.sh
│   ├── dev.sh
│   ├── run.sh
│   ├── rebuild-aggregates.sh
│   └── backup-database.sh
├── tests/
├── AI/                          # Markdown knowledge base and visual references
├── .env.example
├── .gitignore
├── compose.yaml
└── Dockerfile
```

`database/` is mounted into the production container at `/app/database`. No database or Polar payload is stored in an anonymous container layer.

---

## 4. Step-by-Step Implementation Todo List

### Phase A — Foundation and executable skeleton

#### Task 1: Create the backend package and health endpoint

**Files:**
- Create `src/backend/pyproject.toml`
- Create `src/backend/src/polar_app/main.py`
- Create `src/backend/src/polar_app/config.py`
- Create `src/backend/tests/test_health.py`

**Todos:**
- [x] Write a failing `GET /api/health` test.
- [x] Add validated settings for database path, bind host/port, timezone, public base URL, and sync interval.
- [x] Implement the FastAPI application factory and health endpoint.
- [x] Run the backend health tests; all pass.
- [x] Run Ruff and mypy on the package.
- [x] Commit as `feat: initialize FastAPI service`.

**Acceptance:** Running Uvicorn returns JSON containing service status and schema/application version.

#### Task 2: Create the React/Vite shell

**Files:**
- Create `src/frontend/package.json`
- Create `src/frontend/vite.config.ts`
- Create `src/frontend/src/main.tsx`
- Create `src/frontend/src/App.tsx`
- Create `src/frontend/src/App.test.tsx`

**Todos:**
- [x] Write a failing render/navigation test.
- [x] Add routes for `/timeline`, `/training`, `/mappings`, and `/settings`.
- [x] Add the application header and navigation.
- [x] Configure Vite's development proxy for `/api`.
- [x] Run `npm test`; all tests pass.
- [x] Run TypeScript, ESLint, and production build checks.
- [x] Commit as `feat: initialize React application shell`.

#### Task 3: Add portable local and Docker startup

**Files:**
- Create `Dockerfile`
- Create `compose.yaml`
- Create `scripts/dev.sh`
- Create `scripts/build.sh`
- Create `scripts/run.sh`
- Create `.env.example`
- Create/update `.gitignore`
- Create `database/.gitkeep`

**Todos:**
- [x] Build frontend assets in the first Docker stage.
- [x] Copy assets into FastAPI's static directory in the runtime stage.
- [x] Add `scripts/build.sh` to build the browser assets outside Docker and off the `noexec` CIFS share.
- [x] Add `scripts/run.sh` to validate the Python environment/assets, create data directories, apply migrations, and start one Uvicorn worker.
- [x] Add `scripts/dev.sh` to supervise FastAPI and the Vite development server from external cache workspaces.
- [x] Mount `./database:/app/database` in Compose.
- [x] Configure a single backend worker so only one scheduler instance runs.
- [x] Bind native startup to `0.0.0.0` for the trusted home LAN by default, document the `127.0.0.1` override, and preserve the localhost OAuth callback.
- [ ] Verify `docker compose up --build` starts the service.
- [x] Verify natively that the browser loads the React page and `/api/health` through the same port.
- [ ] Stop and restart the container; verify a file created under `database/` persists.
- [x] Commit as `build: add portable application startup`.

### Phase B — Database and core domain model

#### Task 4: Configure SQLite and migrations

**Files:**
- Create `src/backend/src/polar_app/db.py`
- Create `src/backend/src/polar_app/models/base.py`
- Create Alembic configuration under `src/backend/alembic/`
- Create `src/backend/tests/test_database_location.py`

**Todos:**
- [x] Test that the configured database resolves beneath `database/` by default.
- [x] Enable SQLite foreign keys and CIFS-compatible dotfile locking with rollback journaling; keep WAL configurable for compatible local filesystems.
- [x] Add transaction/session dependency handling.
- [x] Create and run the initial migration.
- [x] Verify native startup creates `database/polar-app.sqlite3` and passes `PRAGMA integrity_check`.
- [x] Commit as `feat: add SQLite persistence and migrations`.

#### Task 5: Model raw imports, sessions, sync state, and OAuth tokens

**Files:**
- Create `src/backend/src/polar_app/models/polar.py`
- Create `src/backend/src/polar_app/models/sync.py`
- Create `src/backend/tests/models/test_polar_models.py`
- Create an Alembic migration

**Todos:**
- [x] Add `polar_raw_payloads` with endpoint, external ID, fetched timestamp, payload JSON, and content hash.
- [x] Add `polar_training_sessions` with external ID, sport type, local start/end, duration, distance, average pace, average speed, mean/max heart rate, calories, load, and raw-payload reference.
- [x] Add sleep, Nightly Recharge, daily activity, and heart-rate source tables described in `MAIN.md`.
- [x] Add `polar_sync_state` with last success, last attempt, and error summary.
- [x] Add Fernet-encrypted access-token metadata without storing the Polar account password.
- [x] Add uniqueness constraints so repeated imports are idempotent.
- [x] Test insert, update, deduplication, and foreign-key behavior.
- [x] Commit as `feat: add Polar source data models`.

#### Task 6: Model manual daily context

**Files:**
- Create `src/backend/src/polar_app/models/manual.py`
- Create `src/backend/src/polar_app/schemas/manual.py`
- Create `src/backend/tests/models/test_manual_entries.py`
- Create an Alembic migration

**Todos:**
- [ ] Model daily notes, subjective sleep, mood, stress, illness, medication, caffeine, alcohol, meals, and tags.
- [ ] Keep timed events separate from one-per-day values.
- [ ] Add validation ranges and nullable semantics.
- [ ] Test create/update/delete and date uniqueness.
- [ ] Commit as `feat: add manual daily context model`.

### Phase C — Polar authentication and synchronization

#### Task 7: Verify current Polar API details before coding endpoints

**Files:**
- Update `LINKS.md`
- Update `AI/POLAR_API.md` and `AI/LINKS.md`

**Todos:**
- [x] Verify current v3 OAuth scope and endpoints against official Polar documentation; v4 remains out of scope pending independent verification.
- [x] Verify the registered local `localhost` callback in a real browser flow. A LAN callback is not required while the application retains its registered localhost OAuth origin.
- [x] Identify that the implemented required records use v3.
- [x] Record v3 rate limits, historical availability, backfill limits, and source units in `POLAR_API.md`.
- [x] Implement only documented v3 endpoint paths and scope; defer unverified v4 endpoints.
- [x] Commit as `docs: verify Polar AccessLink integration details`.

#### Task 8: Implement OAuth connection flow

**Files:**
- Create `src/backend/src/polar_app/polar/oauth.py`
- Create `src/backend/src/polar_app/api/oauth.py`
- Create `src/backend/tests/polar/test_oauth.py`

**Todos:**
- [x] Test authorization URL construction and anti-CSRF state handling.
- [x] Implement `/api/polar/connect` and `/api/polar/callback`.
- [x] Test token exchange and required Polar user registration using mocked Polar responses.
- [x] Persist Fernet-encrypted access-token metadata securely; the client secret comes from environment configuration. The documented v3 response does not provide a refresh token.
- [x] Ensure application error messages do not expose secrets or complete tokens.
- [x] Add connection-status and disconnect endpoints.
- [x] Verify callback error paths and real local authorization behavior; the callback host must match the origin host for the state cookie.
- [x] Commit as `feat: add Polar OAuth connection`.

#### Task 9: Implement the resilient Polar client

**Files:**
- Create `src/backend/src/polar_app/polar/client.py`
- Create `src/backend/src/polar_app/polar/exceptions.py`
- Create `src/backend/tests/polar/test_client.py`

**Todos:**
- [x] Add explicit request timeouts.
- [x] Use the documented v3 access token; refresh-token behavior remains out of scope because the v3 token response does not document a refresh token.
- [x] Add bounded retry behavior for retryable failures.
- [x] Respect numeric `Retry-After` when provided.
- [x] Test unauthorized, rate-limited, malformed-response, and success paths.
- [x] Commit as `feat: add resilient Polar API client`.

#### Task 10: Normalize and upsert training sessions

**Files:**
- Create `src/backend/src/polar_app/polar/normalize_training.py`
- Create `src/backend/src/polar_app/polar/sync_training.py`
- Create `src/backend/tests/fixtures/polar/`
- Create `src/backend/tests/polar/test_training_sync.py`

**Todos:**
- [x] Add sanitized fixture payloads from the documented API shape.
- [x] Test conversions for duration, distance, speed, and pace.
- [x] Preserve source timezone/offset and derive configured local date.
- [x] Calculate `duration_pace_index` per session only when duration and valid positive pace exist.
- [x] Store the raw response within the source-data transaction.
- [x] Upsert changed records and leave unchanged records untouched.
- [x] Return inserted/updated/skipped/error counts.
- [x] Commit as `feat: import Polar training sessions`.

#### Task 11: Add sleep, recovery, and activity synchronization

**Files:**
- Create sync/normalization modules under `src/backend/src/polar_app/polar/`
- Create corresponding tests under `src/backend/tests/polar/`

**Todos:**
- [x] Implement one data category at a time: sleep, Nightly Recharge, activity, then continuous heart rate.
- [x] Retain raw responses for every category.
- [x] Make each category idempotent and independently run in separate transactions.
- [x] Add a manual `POST /api/polar/sync` endpoint and `GET /api/polar/status` endpoint.
- [ ] Test partial failure: one category failing must not corrupt successful categories.
- [ ] Commit each category separately.

#### Task 12: Add scheduled synchronization

**Files:**
- Create `src/backend/src/polar_app/scheduler.py`
- Create `src/backend/tests/test_scheduler.py`

**Todos:**
- [x] Schedule sync at a configurable interval, disabled when not connected.
- [x] Prevent overlapping runs within the single scheduler process.
- [ ] Trigger an incremental aggregate refresh after training changes; aggregation is not implemented yet.
- [x] Store last attempt, success, duration, and error message.
- [ ] Test startup, interval, overlap prevention, and shutdown behavior with frozen time.
- [ ] Document the one-worker constraint.
- [x] Commit as `feat: schedule Polar synchronization`.

### Phase D — Training groups and mapping

#### Task 13: Create training-group and mapping models

**Checkpoint (2026-09-03):** Implemented in `models/training_groups.py` and migration `0004_training_groups.py`. Groups have a name, slug, color, position, and enabled flag. Sport types have explicit `mapped`, `unmapped`, and `ignored` states. Aggregate-dirty tracking remains deferred because aggregate archives do not yet exist.

**Files:**
- Create `src/backend/src/polar_app/models/training_groups.py`
- Create `src/backend/tests/models/test_training_groups.py`
- Create an Alembic migration

**Todos:**
- [x] Add user-defined group name, stable slug, display color, position, and enabled flag.
- [x] Add mapping from each Polar sport identifier to zero or one group.
- [x] Represent `unmapped` and `ignored` explicitly rather than using magic group names.
- [ ] Seed an editable `Running` example only if Polar types are discovered; do not assume exact Polar identifiers.
- [ ] Test that multiple Polar types can map to `Running`.
- [ ] Test moving a type between groups and marking it ignored.
- [ ] Mark affected aggregate groups/buckets dirty after mapping changes.
- [x] Commit as `feat: add configurable training groups`.

#### Task 14: Build mapping API

**Checkpoint (2026-09-03):** `api/training_groups.py` implements group list/create, observed sport-type listing with session count/current state, atomic mapping updates, and duplicate-name/slug rejection. Rename, reorder, color update, delete, and reassignment policy remain future work.

**Files:**
- Create `src/backend/src/polar_app/schemas/training_groups.py`
- Create `src/backend/src/polar_app/api/training_groups.py`
- Create `src/backend/tests/api/test_training_groups.py`

**Todos:**
- [ ] Add complete CRUD endpoints for collected groups (list/create implemented; update/delete remain).
- [x] Add endpoint listing all observed Polar sport types with session count and current state.
- [x] Add atomic mapping update endpoint.
- [x] Require an explicit unmapping or reassignment policy when deleting a group; reject missing, self, or unknown replacement groups.
- [ ] Test validation, reassignment, ignore, unmapped, and delete behavior.
- [x] Commit as `feat: expose training group mapping API`.

#### Task 15: Build mapping UI

**Checkpoint (2026-09-04):** `MappingsPage.tsx` creates and lists groups, displays each observed Polar sport type with its session count, warns about unmapped sessions, and assigns each type to a group, `ignored`, or `unmapped` through the atomic mapping API. Group rename, ordering, color selection, and deletion remain deferred.

**Files:**
- Create `src/frontend/src/features/mappings/TrainingMappingPage.tsx`
- Create related API hooks/components/tests

**Todos:**
- [x] List observed Polar types and session counts.
- [ ] Allow group creation, rename, ordering, color selection, and deletion (creation is implemented; the rest remain).
- [x] Provide group, ignored, and unmapped targets for each Polar type.
- [x] Show an explicit warning/count for unknown or unmapped types.
- [x] Confirm destructive group deletion and require reassignment or unmapping.
- [x] Verify keyboard operation and accessible form labels.
- [x] Commit as `feat: add training type mapping interface`.

### Phase E — RRD-style training aggregation

#### Task 16: Add aggregate schema

**Files:**
- Create `src/backend/src/polar_app/models/training_aggregates.py`
- Create `src/backend/tests/models/test_training_aggregates.py`
- Create an Alembic migration

**Todos:**
- [x] Store group, resolution (`day`, `week`, `month`), bucket start/end, timezone, metric means, metric sample counts, and session count.
- [x] Add a unique key on group + resolution + bucket start + timezone.
- [x] Add rebuild metadata/version so aggregation changes can invalidate old rows.
- [x] Test uniqueness and nullable metric behavior.
- [x] Commit as `feat: add training aggregate archives`.

#### Task 17: Implement deterministic bucket boundaries

**Files:**
- Create `src/backend/src/polar_app/aggregation/buckets.py`
- Create `src/backend/tests/aggregation/test_buckets.py`

**Todos:**
- [x] Define day buckets in the configured local timezone.
- [x] Define ISO calendar weeks beginning Monday.
- [x] Define calendar-month buckets.
- [x] Test month/year boundaries, leap day, and daylight-saving transitions.
- [x] Test the exact ranges: 28 days, 26 weeks, and all calendar months.
- [x] Commit as `feat: define aggregate time buckets`.

#### Task 18: Implement aggregate calculation

**Files:**
- Create `src/backend/src/polar_app/aggregation/training.py`
- Create `src/backend/tests/aggregation/test_training.py`

**Todos:**
- [x] Write tests with sessions containing complete and missing metrics.
- [x] Calculate means directly from sessions, never from lower-resolution rows.
- [x] Calculate the per-session duration/pace index before averaging it.
- [x] Exclude null values per metric and store metric-specific sample counts.
- [x] Do not emit misleading zeros for empty buckets.
- [x] Keep empty bucket generation as a presentation concern in the API.
- [x] Verify arithmetic means against hand-calculated fixtures.
- [x] Commit as `feat: calculate training progress aggregates`.

#### Task 19: Add incremental and full aggregate rebuilds

**Files:**
- Create `src/backend/src/polar_app/aggregation/rebuild.py`
- Create `src/backend/src/polar_app/cli.py`
- Create `src/backend/tests/aggregation/test_rebuild.py`
- Create `scripts/rebuild-aggregates.sh`

**Todos:**
- [x] Rebuild affected daily, weekly, and monthly buckets after a session insert/update.
- [x] Rebuild affected groups after mapping changes.
- [x] Delete stale rows when a bucket becomes empty.
- [x] Add an idempotent full rebuild CLI.
- [x] Test incremental output equals a clean full rebuild.
- [x] Test rerunning a rebuild does not change results.
- [x] Commit as `feat: rebuild training aggregate archives`.

#### Task 20: Expose training-series API

**Checkpoint (2026-09-05):** The group route now serves aggregate-backed `GET /api/training/groups/{group_id}/series?range=4w|6m|all` responses: daily, weekly, and monthly buckets respectively, including metric sample counts, total distance, metadata, and explicit empty buckets for chart continuity.

**Files:**
- Create `src/backend/src/polar_app/schemas/training_series.py`
- Create `src/backend/src/polar_app/api/training_series.py`
- Create `src/backend/tests/api/test_training_series.py`

**Todos:**
- [x] Add `GET /api/training/groups/{group_id}/series?range=4w|6m|all`.
- [x] Map `4w` to daily, `6m` to weekly, and `all` to monthly resolution.
- [x] Return ordered buckets with start/end, label, metric values, sample counts, and session count.
- [x] Return explicit null-valued empty buckets for daily/weekly continuity where useful to the chart.
- [x] Include units and aggregation method in response metadata.
- [x] Test range boundaries, missing buckets, unknown groups, and stable ordering.
- [x] Commit as `feat: expose accumulated training series`.

### Phase F — Training progress page

#### Task 21: Create chart-ready API hooks and range controls

**Checkpoint (2026-09-05):** `TrainingPage.tsx` uses typed API hooks, provides group selection and the three range controls, persists the selection in the URL, and renders aggregate-backed chart data and drill-down states.

**Files:**
- Create `src/frontend/src/api/training.ts`
- Create `src/frontend/src/features/training/TrainingRangeSelector.tsx`
- Create tests next to components

**Todos:**
- [x] Add typed data contracts and React Query hooks.
- [x] Add exactly three buttons: `4 weeks`, `6 months`, `All`.
- [x] Persist the selected range in the URL query string.
- [x] Add a group selector, with unmapped counts linked to the mapping page.
- [ ] Test keyboard navigation, URL restoration, loading, empty, and error states.
- [x] Commit as `feat: add training chart controls`.

#### Task 22: Implement synchronized stacked training charts

**Files:**
- Create `src/frontend/src/features/training/TrainingCharts.tsx`
- Create `src/frontend/src/features/training/MetricChart.tsx`
- Create related tests

**Todos:**
- [x] Follow `raw/training-graph.png`: vertically stacked panels with aligned/synchronized date axes.
- [x] Add panels for total distance, mean heart rate, mean pace, mean duration, and mean duration/pace index.
- [x] Keep all panels visible on the same training page, each with an independent border.
- [x] Use linked crosshairs/tooltips across charts, including empty buckets.
- [x] Show bucket date range, value, session count, and metric sample count in tooltips.
- [x] Render gaps for missing values rather than zero lines.
- [x] Format pace as `mm:ss min/km` while keeping numeric values suitable for averaging.
- [ ] Add responsive layout and horizontal zoom/pan only where it remains understandable.
- [ ] Use group color as an accent without making it the only identifier.
- [x] Commit as `feat: add accumulated training progress charts`.

#### Task 23: Add session drill-down

**Files:**
- Create `src/backend/src/polar_app/api/training_sessions.py`
- Create `src/frontend/src/features/training/BucketSessions.tsx`
- Create backend and frontend tests

**Todos:**
- [x] Add a validated backend bucket-session endpoint for mapped contributing sessions.
- [x] Make chart bucket selection load contributing sessions.
- [x] Show date, original Polar type, duration, pace, heart rate, and calculated index.
- [ ] Explain missing values and which sessions contributed to each mean.
- [ ] Link unmapped sessions to the mapping interface.
- [x] Commit as `feat: add training aggregate drill-down`.

### Phase G — Timeline and manual context

#### Task 24: Build the daily timeline API and UI

**Files:**
- Create `src/backend/src/polar_app/api/timeline.py`
- Create `src/frontend/src/features/timeline/TimelinePage.tsx`
- Create associated tests

**Checkpoint (2026-09-06):** `GET /api/timeline` and `TimelinePage.tsx` serve and render a 28-day Polar-backed recovery timeline. It includes normalized sleep/activity/Nightly Recharge data, continuous heart-rate samples, summary tiles, five 28-day metric charts, and a Daily Heart Rate chart whose visible rolling 24-hour window can move backward across imported data. Date/description Timeline events are the implemented manual-context mechanism: they have create, update, and delete APIs; the UI creates them by double-click, manages them after the charts, colors event-day line segments amber without point markers, and includes descriptions in tooltips.

**Todos:**
- [x] Return available sleep, recovery, activity, and continuous heart-rate records grouped by local day.
- [x] Render localized metric tiles and charts with missing-data states.
- [x] Test partial days and missing source categories.
- [ ] Add training integration, selected-day detail, and long-range pagination/virtualization. The 24-hour heart-rate window can already navigate the imported 28-day range; Timeline events cover the current manual-context requirement.
- [x] Commit as `feat: add day-by-day health timeline`.

#### Task 25: Optional structured manual-entry forms

Date-scoped free-text Timeline events are the implemented manual-context feature. Add this separate model only if future requirements need typed, timed, or one-per-day fields beyond those events.

**Files:**
- Create backend manual-entry API routes
- Create `src/frontend/src/features/timeline/ManualEntryForm.tsx`
- Create associated tests

**Todos:**
- [ ] Add forms for meals, caffeine, alcohol, medication, stress, illness, mood, subjective sleep, and notes.
- [ ] Support edit/delete and clear distinction between unknown and zero/none.
- [ ] Validate on both frontend and backend.
- [ ] Confirm entries survive restart and appear on the correct local day.
- [ ] Commit as `feat: add manual daily context entry`.

### Phase H — Runtime light/dark theme

#### Task 26: Implement theme tokens and switch

**Files:**
- Create `src/frontend/src/theme/tokens.css`
- Create `src/frontend/src/theme/ThemeProvider.tsx`
- Create `src/frontend/src/components/ThemeSwitch.tsx`
- Create related tests

**Todos:**
- [ ] Define semantic CSS variables for background, foreground, muted text, cards, borders, accents, success, warning, and error.
- [ ] Support `light`, `dark`, and internal initial `system` detection; expose the requested light/dark runtime switch.
- [ ] Persist the explicit choice in local storage.
- [ ] Update ECharts colors, axes, grids, and tooltips when the theme changes without page reload.
- [ ] Ensure no flash of the wrong theme during startup.
- [ ] Check contrast and focus indicators in both themes.
- [x] Commit as `feat: add runtime light and dark themes`.

### Phase I — Operations, safety, and completion

#### Task 27: Add database backup and restore documentation

**Files:**
- Create `scripts/backup-database.sh`
- Update `README.md`

**Todos:**
- [x] Use SQLite's online backup mechanism rather than copying a live database file blindly.
- [x] Store timestamped backups under `database/backups/`.
- [x] Document restore steps and permissions.
- [x] Test backup integrity with `PRAGMA integrity_check` against the copy.
- [x] Commit as `ops: add SQLite backup procedure`.

#### Task 28: Add end-to-end acceptance tests

**Files:**
- Create `src/frontend/tests-e2e/app.spec.ts`
- Add deterministic seed fixtures/scripts

**Todos:**
- [ ] Seed running/walking sessions spanning days, weeks, months, missing values, and multiple Polar sport types.
- [ ] Verify many-to-one mapping changes chart membership.
- [ ] Verify all three range buttons request/render the correct resolution.
- [ ] Verify means and duration/pace index against fixture expectations.
- [ ] Verify bucket drill-down.
- [ ] Verify light/dark switching persists after reload.
- [ ] Verify manual entries and timeline rendering.
- [ ] Verify database persistence across service restart.
- [ ] Commit as `test: add end-to-end application coverage`.

#### Task 29: Security and operational review

**Files:**
- Update `README.md`, `.env.example`, and deployment configuration

**Todos:**
- [ ] Confirm no OAuth secrets, tokens, raw personal data, databases, backups, or logs are tracked by Git.
- [ ] Confirm token values are redacted from exceptions and logs.
- [x] Document trusted-LAN `0.0.0.0` default, the `127.0.0.1` override, unchanged localhost OAuth callback, and risks of LAN binding.
- [ ] If LAN access is enabled, document reverse-proxy HTTPS and authentication as a prerequisite for access beyond a trusted home network.
- [ ] Confirm no public port forwarding is required for routine operation.
- [ ] Run dependency and container vulnerability checks.
- [ ] Commit as `docs: document secure local deployment`.

#### Task 30: Final release verification

**Todos:**
- [ ] Start from a clean checkout with only Docker/Compose installed and verify the Docker path.
- [ ] Start from a prepared frontend build with the documented Python environment and verify the native path.
- [ ] Run `docker compose up --build`.
- [ ] Run `bash scripts/run.sh` separately against the same `database/` after stopping Docker.
- [ ] Complete or mock the OAuth flow in a controlled test environment.
- [ ] Run a sync twice and verify no duplicates.
- [ ] Verify every mutable artifact is under `database/`.
- [ ] Verify mapping `jogging` and `trail` to `Running` combines both in charts.
- [ ] Compare daily, weekly, and monthly API results against fixture calculations.
- [ ] Verify all four metric panels fit on one page and share aligned time axes.
- [ ] Verify light/dark switching without reload.
- [ ] Run backend tests, frontend tests, type checks, linters, production build, and Playwright tests.
- [ ] Restart the service and verify data/settings remain intact.
- [ ] Tag the first usable local release only after every check passes.

---

## 5. API Outline

```text
GET    /api/health
GET    /api/polar/status
POST   /api/polar/connect
GET    /api/polar/callback
DELETE /api/polar/connection
POST   /api/sync
GET    /api/sync/status

GET    /api/training/groups
POST   /api/training/groups
PATCH  /api/training/groups/{id}
DELETE /api/training/groups/{id}
GET    /api/training/polar-types
PUT    /api/training/polar-types/{polar_type}/mapping
GET    /api/training/groups/{id}/series?range=4w|6m|all
GET    /api/training/groups/{id}/sessions?from=...&to=...

GET    /api/timeline?start=...&end=...
POST   /api/timeline/events
PUT    /api/timeline/events/{id}
DELETE /api/timeline/events/{id}
GET    /api/manual/days/{date}
PUT    /api/manual/days/{date}
POST   /api/manual/events
PATCH  /api/manual/events/{id}
DELETE /api/manual/events/{id}
```

---

## 6. Training-Series Response Contract

Each response should include enough metadata that the frontend does not guess aggregation semantics:

```json
{
  "group": {"id": 1, "name": "Running", "color": "#3b82f6"},
  "range": "6m",
  "resolution": "week",
  "timezone": "Europe/Berlin",
  "aggregation": "arithmetic_mean_of_sessions",
  "metrics": {
    "mean_heart_rate": {"unit": "bpm"},
    "mean_pace": {"unit": "min_per_km"},
    "mean_duration": {"unit": "minutes"},
    "mean_duration_pace_index": {"unit": null}
  },
  "buckets": [
    {
      "start": "2026-08-24",
      "end": "2026-08-31",
      "session_count": 3,
      "mean_heart_rate": 141.3,
      "mean_heart_rate_count": 3,
      "mean_pace": 6.2,
      "mean_pace_count": 3,
      "mean_duration": 42.0,
      "mean_duration_count": 3,
      "mean_duration_pace_index": 6.77,
      "mean_duration_pace_index_count": 3
    }
  ]
}
```

The JSON above defines shape, not real application data.

---

## 7. Validation Commands

Run these without output-truncating pipes so failures are preserved:

```bash
# Backend
cd src/backend
pytest -v
ruff check .
ruff format --check .
mypy src

# Frontend
cd src/frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
npm run test:e2e

# Container/application
cd ..
docker compose build
docker compose up
```

Expected final state: all commands exit with status 0, the web UI is reachable, and service restart preserves the SQLite data in `database/`.

---

## 8. Risks and Tradeoffs

- **Polar API coverage:** Exact v4 scopes/endpoints must be verified before implementation; some historical data may require v3 or may have limited backfill.
- **OAuth callbacks:** Localhost/LAN callback acceptance remains provider-dependent and must be verified in Polar's current client administration.
- **Single scheduler:** APScheduler in the web process is intentionally simple. Running multiple workers would duplicate scheduling unless a separate scheduler/lock architecture is added.
- **Arithmetic means:** A short and long session contribute equally. This matches the stated goal of tracking a typical session, but differs from time-weighted physiological summaries.
- **Pace terminology:** The source requirement says average speed but gives `min/km`, which is pace. The UI will label it as pace while retaining any source speed value separately.
- **Duration/pace index:** The requested metric is shown without a unit. It is calculated per session before averaging to avoid deriving it from unrelated bucket means.
- **Changing mappings:** Remapping a Polar type can alter historical charts. Full deterministic rebuild support makes this safe and explainable.
- **Timezone changes:** Aggregate bucket boundaries depend on the configured timezone; changing it requires a full aggregate rebuild.
- **Chart density:** Four synchronized panels on one page may be tall on small screens. The first version should preserve stacked alignment and allow compact/collapsible panels if usability testing demands it.
- **Continuous heart rate volume:** Store it only after endpoint/rate-limit/storage impact is measured; it is not required for the first training aggregate charts.
- **CIFS execution and locking:** The current share is mounted `noexec`, does not support the symlinks needed by local dependency environments, and rejects SQLite's normal byte-range locking. Repository scripts run through `bash`, place tool workspaces in the host cache, and use SQLite `unix-dotfile` locking with rollback journaling by default.

---

## 9. Definition of Done

- [ ] A new machine can start the application from the project root with Docker Compose.
- [x] A prepared frontend build can start natively through `bash scripts/run.sh` without Docker or a running Node service.
- [ ] Native and Docker modes expose the same features and preserve the same `database/` contents.
- [x] The browser UI and API are served from one configured endpoint.
- [x] All currently implemented mutable data is persisted under `database/`.
- [ ] Polar OAuth and interval synchronization work without storing a Polar password.
- [ ] Repeated synchronization is idempotent.
- [ ] Polar training types can be assigned many-to-one to collected groups, ignored, or left unmapped.
- [ ] Mapping jogging and trail to Running causes both to contribute to Running aggregates.
- [ ] The training page presents all metric graphs as aligned stacked charts.
- [ ] The 4-week, 6-month, and all-history buttons select daily, weekly, and monthly archives respectively.
- [ ] Every metric is an arithmetic mean of contributing session values, with missing values excluded and sample counts disclosed.
- [ ] The duration/pace index is calculated per session and then averaged.
- [ ] Aggregates can be rebuilt exactly from normalized sessions.
- [ ] The day timeline combines Polar and manually entered context.
- [x] Light and dark themes switch at runtime and persist.
- [ ] Automated tests, linters, type checks, build, and end-to-end tests pass.
- [ ] Backup and restore procedures are documented and verified.
