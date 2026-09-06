# Polar Web App

A private, self-hosted dashboard for importing Polar AccessLink data and reviewing recovery, heart-rate, and training trends. It is intended for personal observation and progress tracking, **not** medical diagnosis.

## What it does

- Connects to Polar through OAuth; no Polar account password is stored.
- Syncs Polar data automatically every hour and supports manual sync.
- Shows a Timeline with nightly HRV, heart rate, respiration, ANS charge, Nightly Recharge, and a rolling 24-hour continuous-heart-rate chart when Polar provides the data.
- Shows Training Progress charts for user-defined sport groups: distance, heart rate, pace, duration, and duration/pace index.
- Supports English, German, and Russian plus light/dark themes.
- Stores all local data in SQLite under `database/`.

## Quick start (native)

Requirements:

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm (only needed to build the frontend from source)

```bash
# Install production Python dependencies.
bash scripts/install-python-runtime-libs.sh

# Build browser assets.
bash scripts/build.sh

# Start the app, including migrations and the hourly scheduler.
bash scripts/run.sh
```

Open <http://localhost:8000>.

This checkout may be on a `noexec` CIFS mount. Invoke repository scripts with `bash`, as shown above.

## Connect Polar

1. Create a Polar AccessLink client.
2. Copy `.env.example` to `.env` and set the client credentials, exact redirect URI, and Fernet encryption key.
3. Start the app and open <http://localhost:8000/settings>.
4. Select **Connect Polar**, complete Polar Flow consent, then select **Sync now**.

The complete, GitHub-safe setup guide is [AI/POLAR_AUTH_SETUP.md](AI/POLAR_AUTH_SETUP.md). In particular, keep `.env`, the SQLite database, OAuth tokens, the Polar client secret, and the Fernet key out of Git.

## Short user guide

### Timeline

- The top tiles show the latest nightly value, seven-day average, and comparison where data is available.
- Hover a chart for an exact value and crosshair.
- Double-click a Timeline datapoint to create a dated free-text special event. Event dates are highlighted with a diamond marker and the event appears in the chart tooltip.

### Training Progress

- Create a group on **Mappings** (for example, `Running`).
- Map observed Polar sport types to that group, or leave them unmapped/ignored.
- Open **Training** and choose the group and range (`4 weeks`, `6 months`, or `All`).
- Hover synchronized charts for values; select a bucket to inspect contributing sessions.

### Settings

- **Sync now** imports currently available Polar records and reports new, updated, unchanged, and failed records by category.
- After Polar is connected, the in-process scheduler re-syncs every 60 minutes by default. Set `POLAR_APP_SYNC_INTERVAL_MINUTES` in `.env` to change the interval.

## Development and documentation

Use `bash scripts/install-python-libs.sh` when backend test and development dependencies are also needed. See [AI/DEPLOYMENT.md](AI/DEPLOYMENT.md) for runtime and storage details, and [AI/DOCUMENTATION.md](AI/DOCUMENTATION.md) for the project documentation map.

## Security and privacy

The application is private by default. Do not expose it to the public internet without authentication and HTTPS. Do not commit `.env`, SQLite databases, backups, tokens, credentials, or personal Polar data.
