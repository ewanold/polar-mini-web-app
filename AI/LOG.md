# Log

## 2026-08-23

Initial project notes created.

Current understanding:

- The app should be a local home-server web app.
- The main purpose is personal comparison of Polar sleep data with daily activity and manually entered context.
- The first useful feature should be a scrollable day-by-day visual timeline.
- The official Polar AccessLink API should be used instead of scraping Polar Flow.
- OAuth credentials were expected; later verification established that the implemented v3 flow uses a client ID, client secret, and access token, with no documented refresh token.
- Polar likely uses the normal browser redirect-based OAuth authorization code flow for this setup.
- The setup probably does not require reopening public iptables redirects, because the browser follows the callback URL.
- First try a `localhost` or LAN callback URL for OAuth setup.
- Only expose the home server temporarily if Polar rejects local callback URLs.
- Token storage requirements were later refined to Fernet-encrypted access-token persistence for background sync.
- SQLite is probably sufficient for the first version.
- Raw Polar API responses should be stored together with normalized fields.
- Three PNG files were added as visual references: `screenshot-dashboard.png`, `screenshot-hrv.png`, and `screenshot-experiments.png`.

Open questions:

- Which exact v4 endpoints cover all needed data?
- Are any desired data fields only available through v3?
- Does Polar accept `localhost` or local-network redirect URIs for OAuth client setup?
- If Polar requires a public redirect URI, what is the narrowest safe temporary exposure method?
- Which manual fields are most useful without making daily entry tedious?

## 2026-09-02

- Selected FastAPI, SQLite, React/TypeScript, Vite, Apache ECharts, and Docker Compose as the implementation stack.
- Added a detailed visible implementation plan in `IMPLEMENTATION_PLAN.md`.
- Defined user-managed many-to-one Polar sport mappings, including ignored and unmapped states.
- Defined RRD-inspired daily, weekly, and monthly aggregate archives while retaining normalized source sessions.
- Defined training trends as arithmetic means of session heart rate, pace, duration, and per-session duration/pace index.
- Added `DOCUMENTATION.md` and made the visible Markdown files the durable project knowledge base.
- Reduced `MAIN.md` to core product decisions and moved details into `POLAR_API.md`, `DATA_MODEL.md`, `UI.md`, and `DEPLOYMENT.md`.
- Added `ARCHITECTURE.md` to define the Python/TypeScript boundary, native and Docker modes, single-process scheduler model, request flow, and future separation options.
- Confirmed that Docker is optional: a prepared frontend build can run as one native Python/FastAPI process without a production Node service.
- Implemented the foundation: validated FastAPI settings and health API, SQLAlchemy/Alembic SQLite setup, compiled React/Vite shell with four routes, and persisted runtime themes.
- Added native build, development, and production scripts plus Docker/Compose packaging. Native production and development paths are verified; Compose parses, but container execution remains blocked until the host account can access the Docker daemon.
- Confirmed that the project CIFS share rejects normal SQLite byte-range locking. Switched the default to `unix-dotfile` locking with `DELETE` journaling and kept both settings configurable for compatible local filesystems.
- Verified the native API, SPA fallback and assets, migration revision `0001`, database integrity, backend/frontend tests, linting, type checks, and production frontend build.
- Made repository-root `.env` loading independent of the backend process working directory and added a validated public base URL setting for later OAuth callback generation.
- Moved executable project files out of `AI/`: backend and frontend source now live under project-root `src/`, operational files live at the project root, and `AI/` contains only the Markdown knowledge base and visual references.
- Implemented the Polar AccessLink v3 source-data phase: encrypted OAuth token persistence, OAuth callback and user registration, source-data migrations through `0003`, resilient client behavior, manual and scheduled synchronization, and Settings connection/sync controls.
- Verified a real local OAuth authorization and an initial idempotent source import. The local OAuth callback must use `localhost` consistently because browser state cookies are host-specific.
- Added `POLAR_AUTH_SETUP.md` as the detailed private configuration, troubleshooting, Docker, and GitHub-publication reference. It contains no credentials, tokens, or personal data.

## 2026-09-03

- Added schema revision `0004` with user-managed training groups and explicit Polar sport-type mapping states.
- Implemented group creation/listing, observed-sport-type listing, atomic mapping updates, and a direct mapped-session series endpoint for `4w`, `6m`, and `all` ranges.
- Added initial browser-visible Training Progress and Mapping pages: group creation/listing, three range controls, and clear group/no-mapped-session states.
- Kept materialized aggregate archives, range-specific weekly/monthly bucketing, chart rendering, sport-type assignment controls, and drill-down explicitly as later work.
- Verified the implementation checkpoint with backend tests and Ruff, cached frontend tests/type checking/linting, a production asset build, and local API smoke checks. No personal Polar records or credentials are recorded here.
# 2026-09-04 - Training charts, language foundation, and Polar exercise import

- Added archive-backed training series, ECharts-based stacked metric panels, chart bucket drill-down, and lazy loading for the chart bundle.
- Polar exercise synchronization now follows list references to exercise details and accepts whole-second, clock-style, and fractional-second ISO durations such as `PT3826.778S`.
- Added persisted English/German/Russian UI-language selection with browser-language fallback. The shared shell and Timeline use it; remaining implemented pages still need migration to the catalog.
- The chart tooltip displays metric units and axes use unit-bearing titles. The ECharts pointer remains unresolved: it appears close to a populated point but does not keep tracking through empty daily buckets despite several configuration attempts. No controllable browser was available for live inspection; resume with a screen recording or browser-capable test surface before changing the pointer implementation again.

## 2026-09-06

- Added a GitHub-safe `README.md` with native setup, OAuth setup reference, short user guide, privacy guidance, and trusted-home-LAN access instructions.
- Extended the Daily Heart Rate chart with a 24-hour visible window, initialized at the newest samples and navigable backward across the imported 28-day range.
- Added local Timeline-event update and delete APIs plus an editable/deletable event list below the charts. Events are created by double-click, color matching chart-line segments amber without point markers, and remain visible in tooltips.
- Diagnosed the initial failed event edit as an old Uvicorn process serving code before the update endpoint existed; restarted the service and verified live create (`201`), update (`200`), and delete (`204`) operations.
- Changed native startup to bind `0.0.0.0:8000` by default for a trusted home LAN. The localhost OAuth callback/public URL remain unchanged; the live health endpoint and all-interface listener were verified.
- Recorded the accepted product scope: date-scoped free-text Timeline events are the implemented manual-context feature, and the verified Polar v3 API is complete for the current application; LAN callbacks and v4 remain deferred extensions rather than release blockers.
- Added `scripts/backup-database.sh` and `polar_app.backup`: it uses SQLite's online backup API, verifies `PRAGMA integrity_check`, writes timestamped backups, and was exercised successfully against the live local database. Restore steps are documented in `DEPLOYMENT.md`.
- Verified the focused backend Timeline tests, frontend test/typecheck/lint, production frontend build, backend Ruff, and staged-file whitespace for the related changes. Browser automation could not start Chromium in this environment.

## 2026-09-05

- Completed English, German, and Russian translation coverage for the implemented Training, Mappings, Settings, Timeline, theme, chart, drill-down, validation, loading, empty, error, and synchronization interfaces.
- Added typed interpolation for translated values, localized synchronization category summaries, and compile-time catalog key parity checks for German and Russian.
- Verified all 11 frontend tests, TypeScript type checking, ESLint, and the production Vite build. Live browser inspection remained unavailable because the browser session required interactive remote-debugging permission.
- Fixed the Training Progress crosshair root cause: ECharts represents missing line values as the string `"-"` in tooltip callback data, while the formatter handled only `null` and called numeric formatters on the marker. The formatter now treats every non-finite, non-number value as missing.
- Added a focused regression test and verified the production app in headless Chromium against live API bucket structure: the linked pointer and tooltip moved from a populated bucket to the following empty bucket. All 13 frontend tests, type checking, linting, and the production build pass.
- Added safe training-group deletion. The Mapping UI now requires confirmation and offers explicit unmapping or reassignment of mapped Polar sport types. The API rebuilds the replacement group's aggregates before deletion; unmapping removes the deleted group's aggregate rows. Backend tests cover both paths and frontend tests cover both confirmation flows.
- Added a fifth synchronized Training Progress graph for total distance per range bucket. Training aggregates now retain the distance sum in meters, the series API exposes it, and the chart renders values and tooltips in kilometers while preserving empty buckets.
- Implemented the Polar-backed Timeline: 28-day nightly recovery charts, five localized nightly summary tiles, and a rolling 24-hour Continuous Heart Rate chart. The tiles use a shared localized heading rather than repeating “last night” in every label. Available values are displayed without fabricating missing ANS charge or Nightly Recharge status.
- Refined Training chart cards into five independently bordered panels with internal title/axis spacing and readable x-axis labels.
- Fixed a CIFS SQLite lifecycle issue: reapplying the database-global journal-mode pragma for every new connection could lock the Timeline API. It now runs only on the engine's first connection. A stale dotfile-VFS lock directory left by a force-killed process was removed after confirming no application process held the database; native startup and `GET /api/timeline` were then verified.
