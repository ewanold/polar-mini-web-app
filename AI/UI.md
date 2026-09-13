# User Interface

## Primary Navigation

- Daily timeline
- Training progress
- Training type mappings
- Settings/synchronization status

The implemented application provides four responsive routes with accessible navigation. Settings has working Polar connection/synchronization controls. Training provides range controls, group selection, mapped-session drill-down, and five synchronized ECharts panels. Mappings provides group creation/listing, sport-type assignment, and safe group deletion. Timeline provides Polar-backed recovery and continuous-heart-rate visualizations plus dated free-text event creation and management.

## Settings and Synchronization

Settings fetches `GET /api/polar/status` and displays the current connection state. When disconnected, it provides **Connect Polar**, a browser navigation to `/api/polar/connect`. When connected, it provides **Sync now**, displays the last successful scheduled or manual synchronization in the browser's local date/time format, and refreshes status every minute so later scheduler results appear without a page reload. Manual sync posts to `/api/polar/sync`, prevents a duplicate click while pending, records a successful all-category completion, and displays every category's new, updated, unchanged, and error counts.

The flow is intentionally initiated from the browser so Polar owns the login and consent screen. The browser never receives the OAuth client secret, access token, or Fernet token-encryption key. See `POLAR_AUTH_SETUP.md` for the configuration and callback-host requirement.

## Daily Timeline

The implemented Timeline requests 28 days of normalized Polar sleep, activity, Nightly Recharge, and continuous-heart-rate data. It shows a shared localized **Last night** heading above five metric tiles (HRV, nightly heart rate, respiration, ANS charge, and the Polar-app-style 0–100 nightly/sleep score), a rolling 24-hour heart-rate chart that crosses midnight, and 28-day charts for the five nightly metrics. The Daily Heart Rate chart initially displays the newest 24-hour window; its slider and inside pan navigate backward through the imported 28-day sample range. Tiles show the latest value, seven-day average, and a favorable/unfavorable percentage badge. Missing Polar-calculated ANS charge values remain empty rather than being synthesized; the Nightly Recharge tile/chart uses the normalized sleep score instead of the categorical `nightly_recharge_status` value from the AccessLink Nightly Recharge endpoint.

Timeline and Training charts use ECharts with labeled axes, thin lines, hover crosshairs, and exact-value tooltips. Every actual value is marked by a small circle. Solid lines join adjacent real values; dotted lines bridge internal missing intervals. When synchronization succeeded beyond the latest available value, a dotted horizontal segment carries that value through `synced_through`; the segment is explicitly presentation continuity, not a synthetic measurement. All five nightly Timeline panels use one shared date domain beginning with the earliest available nightly metric, so a metric such as ANS charge retains empty dates before its first value instead of shifting its x-axis start. Nightly axes use compact `MM-DD` labels; the 24-hour heart-rate axis continues to use clock times. The five Training panels retain independent borders and have linked x-axis pointers/tooltips plus synchronized horizontal zoom/pan behavior.

Double-clicking a Timeline chart datapoint opens a free-text event prompt for that datapoint's date. Events are local date/description records, shown in an editable/deletable list after the charts. A visible **Add event** action below the event area opens explicit date and description fields; at phone width the action is fixed near the bottom edge and the form opens as a bottom sheet. An event date changes the matching solid line segment to amber, and its description is included in hover tooltips.

Timeline events provide the implemented date-scoped manual context. Add typed daily/timed entries only if future requirements exceed a date and free-text description.

## Training Progress Page

The page presents accumulated training trends for a selected user-defined group such as Running or Walking. All metric charts are vertically stacked on the same page with aligned time axes, following the overall structure of `raw/training-graph.png`.

The implementation provides `4 weeks`, `6 months`, and `All` controls, group selection persisted in the URL, aggregate-backed buckets, and contributing-session drill-down. Five vertically stacked panels render total distance, mean heart rate, mean pace, mean duration, and mean duration/pace index.

Charts:

1. Total distance (`km`)
2. Mean session heart rate (`bpm`)
3. Mean session pace (`min/km`)
4. Mean session duration (`h:mm` y-axis labels; title remains minutes for the stored value unit)
5. Mean session duration/pace index (no displayed unit)

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
- Circles at every bucket containing an actual metric value
- Dotted connections across internal empty buckets and a dotted horizontal carry-forward through the last successful sync date
- Total distance plotted in kilometers even though the API/storage field is meters
- Pace y-axis and tooltips formatted as `mm:ss min/km`
- Duration y-axis and tooltips formatted as `h:mm`
- Group color used as an accent, never as the only identifier
- Responsive sizing and accessible labels
- Bucket selection opens the contributing sessions for inspection

The reference image contains stacked panels for heart rate, pace, and elevation with synchronized horizontal time alignment and restrained grid lines. It is inspiration, not a fixed visual specification. Elevation is not part of the initial accumulated page unless later requested.

## Training-Type Mapping Page

The Mapping page creates and lists groups, displays every observed Polar sport type with session count/current mapping, warns about unmapped sessions, and assigns each type to a group, `ignored`, or `unmapped`. Group deletion requires explicit reassignment or unmapping of its mapped sport types; the corresponding aggregates are rebuilt or removed safely.

- Create and delete collected groups.
- List every observed Polar sport type with session count and current mapping.
- Assign multiple Polar types to one collected group.
- Mark a type ignored or return it to unmapped.
- Show unknown types prominently instead of silently assigning them.
- Group rename, ordering, color selection, and enabled-state controls remain future work.

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
