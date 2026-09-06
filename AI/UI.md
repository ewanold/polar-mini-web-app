# User Interface

## Primary Navigation

- Daily timeline
- Training progress
- Training type mappings
- Settings/synchronization status

The implemented application provides four responsive routes with accessible navigation. Settings has working Polar connection/synchronization controls. Training provides range controls, group selection, mapped-session drill-down, and five synchronized ECharts panels. Mappings provides group creation/listing, sport-type assignment, and safe group deletion. Timeline provides Polar-backed recovery and continuous-heart-rate visualizations; manual context forms remain future work.

## Settings and Synchronization

Settings fetches `GET /api/polar/status` and displays the current connection state. When disconnected, it provides **Connect Polar**, a browser navigation to `/api/polar/connect`. When connected, it provides **Sync now**, which posts to `/api/polar/sync`, prevents a duplicate click while pending, and displays every category's new, updated, unchanged, and error counts.

The flow is intentionally initiated from the browser so Polar owns the login and consent screen. The browser never receives the OAuth client secret, access token, or Fernet token-encryption key. See `POLAR_AUTH_SETUP.md` for the configuration and callback-host requirement.

## Daily Timeline

The implemented Timeline requests 28 days of normalized Polar sleep, activity, Nightly Recharge, and continuous-heart-rate data. It shows a shared localized **Last night** heading above five metric tiles (HRV, nightly heart rate, respiration, ANS charge, and Nightly Recharge), a rolling 24-hour heart-rate chart that crosses midnight, and 28-day charts for the five nightly metrics. Tiles show the latest value, seven-day average, and a favorable/unfavorable percentage badge. Missing Polar-calculated ANS charge and Nightly Recharge values remain empty rather than being synthesized.

Timeline and Training charts use ECharts with labeled axes, thin lines, hover crosshairs, and exact-value tooltips. The five Training panels have independent borders; charts reserve internal padding for titles and axis labels.

Right-clicking a Timeline chart datapoint opens a free-text event prompt for that datapoint's date. Saved events are marked with an amber diamond on matching chart datapoints and included in the hover tooltip.

Manual context, date-range navigation, selected-day detail, and manual-entry editing remain future work.

## Training Progress Page

The page presents accumulated training trends for a selected user-defined group such as Running or Walking. All metric charts are vertically stacked on the same page with aligned time axes, following the overall structure of `raw/training-graph.png`.

The implementation provides `4 weeks`, `6 months`, and `All` controls, group selection persisted in the URL, aggregate-backed buckets, and contributing-session drill-down. Five vertically stacked panels render total distance, mean heart rate, mean pace, mean duration, and mean duration/pace index.

Charts:

1. Mean session heart rate (`bpm`)
2. Mean session pace (`min/km`)
3. Mean session duration (`minutes`)
4. Mean session duration/pace index (no displayed unit)

Controls:

- Training-group selector
- `4 weeks` button for daily data
- `6 months` button for weekly data
- `All` button for monthly data
- Link/warning showing unmapped Polar sport types

Chart behavior:

- Shared date alignment and linked crosshair/tooltips
- Tooltip with bucket range, metric value, contributing metric sample count, and total session count
- Gaps rather than zeros for missing metrics
- Pace formatted as `mm:ss min/km`
- Group color used as an accent, never as the only identifier
- Responsive sizing and accessible labels
- Bucket selection opens the contributing sessions for inspection

The reference image contains stacked panels for heart rate, pace, and elevation with synchronized horizontal time alignment and restrained grid lines. It is inspiration, not a fixed visual specification. Elevation is not part of the initial accumulated page unless later requested.

## Training-Type Mapping Page

The current initial implementation creates and lists training groups. The backend already exposes observed sport types and atomic mapping updates, but the browser interface for displaying those types and assigning them is not implemented yet.

- Create, rename, reorder, recolor, enable, and delete collected groups.
- List every observed Polar sport type with session count and current mapping.
- Assign multiple Polar types to one collected group.
- Mark a type ignored or return it to unmapped.
- Show unknown types prominently instead of silently assigning them.
- Require reassignment or unmapping before deleting a group that has mappings.
- Rebuild affected aggregate history after mapping changes.

## Manual Context

Support daily and timed entries for meals, caffeine, alcohol, medication, stress, illness, mood, subjective sleep quality, tags, and free-form notes. Distinguish missing/unknown values from explicit zero or none.

## Themes

Provide runtime light and dark themes using semantic CSS custom properties. Persist the explicit choice locally and use system preference only for the initial choice.

The foundation theme switch and local persistence are implemented and covered by component tests. ECharts-specific theme integration remains part of the chart implementation.

Theme changes must update:

- Page and card backgrounds
- Foreground and muted text
- Borders and focus states
- Status colors
- ECharts lines, axes, grids, crosshair, and tooltips

Switching themes must not require a reload and should not flash the wrong theme at startup.

## Visual References

- `raw/screenshot-dashboard.png` — overview/dashboard inspiration
- `raw/screenshot-hrv.png` — recovery/HRV inspiration
- `raw/screenshot-experiments.png` — experiment/comparison inspiration
- `raw/training-graph.png` — synchronized stacked training-chart inspiration

These references guide visual density and organization; usability and the documented product behavior take precedence.
