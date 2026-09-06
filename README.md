# Personal Note

This project began as an experiment for two reasons:

- Last year, I entered my sixties and felt an urgent need to do more for my health. I bought a Polar watch to keep an eye on my training heart rate and overall progress.

  Polar offers several ways to review training data, but it is spread across several pages in the smartphone app and on the website. I wanted the most important information in one place.

- I have been programming for more than four decades and have created some successful open-source software. But this is the age of AI: what can it do, how quickly can it do it, and what could a non-programmer achieve?

  Short answer: a skilled programmer can achieve a lot very quickly, even with limited domain knowledge. This app took perhaps ten working hours to implement. It was mainly slowed down by Codex usage limits: five hours’ worth of tokens could sometimes be consumed in 30 minutes. I used GPT-Sol for planning and mostly GPT-Terra for coding.

  A non-programmer would probably have failed, at least with my approach. I had to help Codex by clarifying details, debugging, moving text around, setting up a Polar account, and finally enabling remote debugging in Chrome.

For these reasons, I decided to put my Codex account to good use and have an agent implement a web-based progress monitor based on my personal Polar data. The app itself is simple and has four tabs:

- **Settings** connects to Polar services and starts a manual sync.

  ![Settings page](screenshots/settings.png)

- **Mappings** maps Polar’s different training names to one group. For example, Polar has Running, Jogging, Trail Running, and so on; I summarize them all as Running.

  ![Mappings](screenshots/mappings.png)

- **Training** shows summaries of training sessions: distance, average heart rate, average pace, duration, and an additional index that divides duration by pace.

  ![Training](screenshots/training.png)

- **Timeline** shows daily heart-rate activity and values based on sleep data.

  The five tiles at the top contain the previous night’s values for:

  - Heart-rate variability
  - Average heart rate
  - Average respiration rate
  - **ANS charge**, a Polar recovery rating based on autonomic-nervous-system data
  - **Nightly Recharge**, Polar’s assessment of recovery from the previous night’s sleep

  **ANS charge** and **Nightly Recharge** are Polar-specific values.

  Below the tiles is the continuous Daily Heart Rate chart collected while wearing the watch during the day. The charts that follow show HRV, heart rate, and other nightly metrics over the previous 28 days.

  ![Timeline](screenshots/timeline.png)

One feature is not immediately obvious: hovering over a chart shows the recorded value at that time. Double-click a data point to add a description of a special event that might affect sleep or recovery. Think of it as a simple diary: for example, you might use it to investigate whether drinking coffee affects your sleep. Hover over the charts to see events recorded for that day. On event days, the affected line segment changes colour.

All events are listed at the bottom of the Timeline, where you can edit or delete them.

![Events](screenshots/events.png)

**If you plan to modify this app**, perhaps to connect it to Garmin, use the AI project documentation. It contains the material I developed with the AI: planning details, todos, and logs. Load [MAIN.md](AI/MAIN.md) into your agent and explain what you want to change; it contains the links needed to understand the app.

The remainder of this README, like every file in this project, was generated with AI. I did not write a single line myself, although I did read parts of it to learn about the internals. :-)

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

Open <http://localhost:8000> on the server, or `http://<server-LAN-IP>:8000` from another device on the trusted home network. Keep Polar OAuth on the server's `localhost` URL; network binding does not change its callback configuration.

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
- Double-click a Timeline datapoint to create a dated free-text special event. Event dates change the chart line color and the event appears in the hover tooltip; manage existing events at the bottom of the Timeline.

### Training Progress

- Create a group on **Mappings** (for example, `Running`).
- Map observed Polar sport types to that group, or leave them unmapped/ignored.
- Open **Training** and choose the group and range (`4 weeks`, `6 months`, or `All`).
- Hover synchronized charts for values; select a bucket to inspect contributing sessions.

### Settings

- **Sync now** imports currently available Polar records and reports new, updated, unchanged, and failed records by category.
- Settings shows the time of the last successful scheduled sync and refreshes that status every minute while open.
- After Polar is connected, the in-process scheduler re-syncs every 60 minutes by default. Set `POLAR_APP_SYNC_INTERVAL_MINUTES` in `.env` to change the interval.

## Backups

Create an online, integrity-checked SQLite backup while the application is running:

```bash
bash scripts/backup-database.sh
```

The command prints the new file under `database/backups/`. Restore instructions and safety checks are in [AI/DEPLOYMENT.md](AI/DEPLOYMENT.md). Backups contain personal health data and must remain outside Git.

## Development and documentation

Use `bash scripts/install-python-libs.sh` when backend test and development dependencies are also needed. See [AI/DEPLOYMENT.md](AI/DEPLOYMENT.md) for runtime and storage details, and [AI/DOCUMENTATION.md](AI/DOCUMENTATION.md) for the project documentation map.

## Security and privacy

The application is private by default. Do not expose it to the public internet without authentication and HTTPS. Do not commit `.env`, SQLite databases, backups, tokens, credentials, or personal Polar data.
