# Data Model and Aggregation

## Storage Principle

All mutable application data belongs under `database/`. The initial implementation uses `database/polar-app.sqlite3`; backups and optional file logs use subdirectories beneath `database/`.

Raw Polar payloads and normalized records are both retained. Raw payloads allow later recovery of fields without depending on another download, while normalized tables support efficient views and aggregates.

## Table Areas

```text
polar_sync_state
polar_raw_payloads
polar_oauth_tokens
polar_sleep_days
polar_nightly_recharge
polar_training_sessions
polar_activity_days
polar_heart_rate_samples

# Training Progress tables
training_groups
polar_sport_type_mappings

# Planned tables
manual_day_entries
manual_events
manual_tags
```

Implemented tables at schema revision `0007` are `polar_sync_state`, `polar_raw_payloads`, `polar_oauth_tokens`, `polar_sleep_days`, `polar_nightly_recharge`, `polar_training_sessions`, `polar_activity_days`, `polar_heart_rate_samples`, `training_groups`, `polar_sport_type_mappings`, and `training_aggregates`. `polar_nightly_recharge` stores nightly heart-rate, HRV, respiration, ANS charge, and Nightly Recharge status when Polar supplies them. `training_aggregates` stores total distance in addition to the metric means and counts. Sleep samples and manual-context tables remain planned.

`polar_oauth_tokens` stores the Polar user identifier, token type, optional expiry, timestamps, and a Fernet-encrypted access token. The encryption key is environment configuration, never database content or a committed secret. See `POLAR_AUTH_SETUP.md` for key lifecycle and recovery behavior.

## Training Sessions

A normalized session should retain, where available:

- Stable Polar external identifier
- Original Polar sport type identifier and display name
- Source start/end timestamp and offset
- Configured local date
- Duration
- Distance
- Average speed
- Average pace in minutes per kilometre
- Mean and maximum heart rate
- Calories and training load
- Link to the raw payload

The application calculates this per-session index when both values are valid:

```text
duration_pace_index = duration_minutes / pace_minutes_per_km
```

The index is displayed without a unit, as requested. Missing or non-positive pace produces a missing index rather than zero.

## Training Groups and Mapping

- Groups are user-managed and have a name, stable identifier, display color, order, and enabled state.
- Multiple Polar sport types can map to one collected group.
- A Polar sport type maps to at most one group.
- A type can be explicitly ignored or remain unmapped.
- Unknown types appear as unmapped until reviewed.
- Mapping changes rebuild affected aggregate history before the updated chart series is served.

Example:

```text
Polar jogging -----+
Polar trail -------+--> Running
Polar road running-+
```

## RRD-Inspired Aggregate Archives

`GET /api/training/groups/{group_id}/series?range=4w|6m|all` serves aggregate-backed chart buckets. `4w` uses daily buckets, `6m` weekly buckets, and `all` monthly buckets, including explicit empty positions for chart continuity. Each bucket includes total distance, metric values, metric sample counts, and total session count.

Normalized sessions remain the source of truth. Rebuildable aggregate tables provide fixed chart resolutions:

| UI mode | Resolution | Requested period |
|---|---|---|
| 4 weeks | Calendar day | Last 28 local calendar days |
| 6 months | ISO calendar week | Last 26 weeks |
| All | Calendar month | All available history |

Unlike a strict RRD database, source sessions are not discarded. Daily, weekly, and monthly rows are materialized caches that can be recreated after formula, timezone, or mapping changes.

## Aggregation Semantics

For each group and bucket:

1. Select mapped sessions by configured local start date.
2. Calculate the duration/pace index per session.
3. Calculate arithmetic means independently for:
   - Session mean heart rate
   - Session average pace
   - Session duration
   - Session duration/pace index
4. Exclude null values separately for each metric.
5. Store session count and metric-specific sample counts.
6. Never substitute zero for missing data.
7. Calculate every resolution directly from sessions, not from lower-resolution means, to avoid average-of-averages bias.

The purpose is to show changes in a typical session, not accumulated training volume. Short and long sessions therefore contribute equally to each arithmetic mean.

## Bucket Rules

- Day buckets follow the configured local timezone.
- Week buckets are ISO weeks beginning Monday.
- Month buckets are calendar months.
- Timezone changes require a full aggregate rebuild.
- Empty daily/weekly positions may be added by the API for continuous axes but are represented with null metrics, not persisted as false zero training.

## Integrity and Lifecycle

- Stable external IDs and unique constraints make sync idempotent.
- Session and mapping changes refresh affected day, week, and month aggregate buckets.
- A full rebuild command must produce the same result as incremental maintenance.
- SQLite foreign keys are enabled. The current CIFS deployment defaults to the `unix-dotfile` VFS and `DELETE` journal mode because normal byte-range locking fails on the share; WAL remains an opt-in setting for compatible local filesystems.
- Schema changes use Alembic migrations.
- Backups must use SQLite's online backup mechanism and be integrity-checked.
