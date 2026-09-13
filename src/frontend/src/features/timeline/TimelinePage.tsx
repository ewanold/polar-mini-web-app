import ReactECharts from "echarts-for-react";
import { FormEvent, useState } from "react";

import { useTimeline, type TimelineDay, type TimelineEvent, type TimelineNightlyRecharge } from "../../api/timeline";
import { timeLineSeries } from "../../components/chartSeries";
import { useLanguage } from "../../i18n/useLanguage";

type Metric = keyof TimelineNightlyRecharge | "sleep_score";
type Tile = { labelKey: "nightlyHrv" | "nightlyHeartRate" | "respiration" | "ansCharge" | "categoryNightlyRecharge"; metric: Metric; unit: string; favourable: "higher" | "lower" };
const tiles: Tile[] = [
  { labelKey: "nightlyHrv", metric: "heart_rate_variability_avg", unit: "ms", favourable: "higher" },
  { labelKey: "nightlyHeartRate", metric: "heart_rate_avg", unit: "bpm", favourable: "lower" },
  { labelKey: "respiration", metric: "breathing_rate_avg", unit: "breaths/min", favourable: "lower" },
  { labelKey: "ansCharge", metric: "ans_charge", unit: "score", favourable: "higher" },
  { labelKey: "categoryNightlyRecharge", metric: "sleep_score", unit: "score", favourable: "higher" },
];

function mean(values: Array<number | null>) { const usable = values.filter((value): value is number => value !== null); return usable.length ? usable.reduce((sum, value) => sum + value, 0) / usable.length : null; }
function nightlyValues(days: TimelineDay[], metric: Metric) { return days.map((day) => metric === "sleep_score" ? day.sleep?.score ?? null : day.nightly_recharge?.[metric] ?? null); }
function nightlyDomainStart(days: TimelineDay[], fallback: string) { return days.find((day) => tiles.some((tile) => (tile.metric === "sleep_score" ? day.sleep?.score : day.nightly_recharge?.[tile.metric]) !== null && (tile.metric === "sleep_score" ? day.sleep?.score : day.nightly_recharge?.[tile.metric]) !== undefined))?.date ?? fallback; }
function compactLocalDate(value: number) { const date = new Date(value); return `${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
function unitFor(tile: Tile, t: ReturnType<typeof useLanguage>["t"]) { return tile.unit === "breaths/min" ? t("breathsPerMinute") : tile.unit; }

function MetricTile({ tile, days }: { tile: Tile; days: TimelineDay[] }) {
  const { t } = useLanguage(); const unit = unitFor(tile, t); const values = nightlyValues(days, tile.metric); const current = [...values].reverse().find((value): value is number => value !== null) ?? null; const average = mean(values.slice(-7)); const change = current !== null && average !== null && average !== 0 ? (current / average - 1) * 100 : null; const favourable = change !== null && (tile.favourable === "higher" ? change >= 0 : change <= 0);
  return <article className="timeline-summary-tile"><p>{t(tile.labelKey)}</p><strong>{current === null ? "–" : current.toFixed(1)}<small>{unit}</small></strong><span>{t("sevenDayAverage", { value: average === null ? "–" : average.toFixed(1), unit })}</span>{change !== null ? <em className={favourable ? "positive" : "negative"}>{t("percentageVsAverage", { arrow: change >= 0 ? "▲" : "▼", value: Math.abs(change).toFixed(0) })}</em> : null}</article>;
}

function LineChart({ title, unit, points, events, className, syncedThrough, domainStart, rolling24Hours = false }: { title: string; unit: string; points: Array<[string, number]>; events: TimelineEvent[]; className: string; syncedThrough: string | null; domainStart?: string; rolling24Hours?: boolean }) {
  const { t } = useLanguage();
  if (!points.length) return <section className={className}><h2>{title}</h2><p>{t("noPolarNightlyData")}</p></section>;
  const eventsFor = (value: string) => events.filter((event) => event.date === value.slice(0, 10)).map((event) => event.description).join("; ");
  const addEvent = async (value: string) => { const description = window.prompt(t("newEventPrompt", { date: value.slice(0, 10) })); if (!description?.trim()) return; await fetch("/api/timeline/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ date: value.slice(0, 10), description }) }); window.location.reload(); };
  const syncedEndpoint = syncedThrough === null ? null : rolling24Hours ? `${syncedThrough}T23:59:59` : syncedThrough;
  const viewEnd = syncedEndpoint && new Date(syncedEndpoint).getTime() > new Date(points.at(-1)![0]).getTime() ? syncedEndpoint : points.at(-1)![0];
  const initialStart = rolling24Hours ? new Date(new Date(viewEnd).getTime() - 86_400_000).toISOString() : undefined;
  const eventDates = new Set(events.map((event) => event.date));
  const series = timeLineSeries({
    points,
    color: "#006f7b",
    gapThresholdMs: 36 * 60 * 60 * 1000,
    syncedThrough: syncedEndpoint,
    colorForDate: (value) => eventDates.has(value.slice(0, 10)) ? "#d97706" : "#006f7b",
  });
  return <section className={className}><h2>{title}</h2><ReactECharts style={{ height: 230 }} onEvents={{ dblclick: (params: { value?: [string, number] }) => { if (params.value?.[0]) void addEvent(params.value[0]); } }} option={{ animation: false, grid: { left: 52, right: 18, top: 20, bottom: rolling24Hours ? 62 : 40 }, dataZoom: rolling24Hours ? [{ type: "inside", startValue: initialStart, endValue: viewEnd }, { type: "slider", startValue: initialStart, endValue: viewEnd, height: 18, bottom: 12 }] : undefined, tooltip: { trigger: "axis", axisPointer: { type: "cross" }, formatter: (items: Array<{ axisValueLabel: string; value: [string, number] }>) => `${items[0]?.axisValueLabel}<br/>${items[0]?.value[1].toFixed(1)} ${unit}${eventsFor(items[0]?.value[0] ?? "") ? `<br/>${eventsFor(items[0]?.value[0] ?? "")}` : ""}` }, xAxis: { type: "time", min: domainStart ?? points[0][0], max: viewEnd, axisLabel: { hideOverlap: true, formatter: (value: number) => rolling24Hours ? new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : compactLocalDate(value) } }, yAxis: { type: "value", name: unit, scale: true }, series }} /></section>;
}

function TimelineEvents({ events }: { events: TimelineEvent[] }) {
  const { t } = useLanguage();
  const editEvent = async (event: TimelineEvent) => { const description = window.prompt(t("editEventPrompt", { date: event.date }), event.description); if (!description?.trim() || description.trim() === event.description) return; const response = await fetch(`/api/timeline/events/${event.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ description }) }); if (!response.ok) { window.alert(t("eventSaveFailed")); return; } window.location.reload(); };
  const deleteEvent = async (event: TimelineEvent) => { if (!window.confirm(t("deleteEventConfirm", { description: event.description }))) return; const response = await fetch(`/api/timeline/events/${event.id}`, { method: "DELETE" }); if (!response.ok) { window.alert(t("eventDeleteFailed")); return; } window.location.reload(); };
  if (!events.length) return null;
  return <section className="timeline-events"><h2>{t("events")}</h2><ul>{events.map((event) => <li key={event.id}><time dateTime={event.date}>{event.date}</time><span>{event.description}</span><button type="button" aria-label={t("editEvent", { description: event.description })} onClick={() => void editEvent(event)}>{t("edit")}</button><button className="danger-button" type="button" aria-label={t("deleteEvent", { description: event.description })} onClick={() => void deleteEvent(event)}>{t("delete")}</button></li>)}</ul></section>;
}

function AddTimelineEvent({ defaultDate, onCreated }: { defaultDate: string; onCreated: () => Promise<unknown> }) {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState(defaultDate);
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedDescription = description.trim();
    if (!date || !trimmedDescription) return;
    setSaving(true);
    setFailed(false);
    const response = await fetch("/api/timeline/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ date, description: trimmedDescription }) });
    if (!response.ok) {
      setSaving(false);
      setFailed(true);
      return;
    }
    await onCreated();
    setDescription("");
    setSaving(false);
    setOpen(false);
  };
  return <section className={`timeline-add-event${open ? " open" : ""}`}>
    <button className="timeline-add-event-button" type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>{t("addEvent")}</button>
    {open ? <form onSubmit={(event) => void submit(event)}>
      <label htmlFor="timeline-event-date">{t("date")}</label>
      <input id="timeline-event-date" type="date" required value={date} onChange={(event) => setDate(event.target.value)} />
      <label htmlFor="timeline-event-description">{t("description")}</label>
      <textarea id="timeline-event-description" required value={description} onChange={(event) => setDescription(event.target.value)} />
      {failed ? <p role="alert">{t("eventSaveFailed")}</p> : null}
      <div><button type="submit" disabled={saving}>{t("saveEvent")}</button><button type="button" onClick={() => setOpen(false)}>{t("cancel")}</button></div>
    </form> : null}
  </section>;
}

function NightlyChart({ tile, days, syncedThrough, domainStart }: { tile: Tile; days: TimelineDay[]; syncedThrough: string | null; domainStart: string }) { const { t } = useLanguage(); return <LineChart className="timeline-chart" title={t(tile.labelKey)} unit={unitFor(tile, t)} events={days.flatMap((day) => day.events ?? [])} points={days.flatMap((day) => { const value = tile.metric === "sleep_score" ? day.sleep?.score : day.nightly_recharge?.[tile.metric]; return value === null || value === undefined ? [] : [[day.date, value] as [string, number]]; })} syncedThrough={syncedThrough} domainStart={domainStart} />; }
function DailyHeartRateChart({ days, syncedThrough }: { days: TimelineDay[]; syncedThrough: string | null }) { const { t } = useLanguage(); const points = days.flatMap((day) => day.heart_rate?.samples ?? []).map((sample) => [sample.sampled_at, sample.heart_rate] as [string, number]); return <LineChart className="timeline-day-heart-rate" title={t("dailyHeartRate")} unit="bpm" events={days.flatMap((day) => day.events ?? [])} points={points} syncedThrough={syncedThrough} rolling24Hours />; }

export function TimelinePage() { const { t } = useLanguage(); const query = useTimeline(); const days = query.data?.days ?? []; const events = days.flatMap((day) => day.events ?? []); const domainStart = query.data ? nightlyDomainStart(days, query.data.start) : ""; return <section aria-labelledby="timeline-title" className="page-panel"><p className="eyebrow">{t("dailyTimeline")}</p><h1 id="timeline-title">{t("dailyTimeline")}</h1>{query.isLoading ? <p>{t("timelineLoading")}</p> : null}{query.isError ? <p role="alert">{t("timelineError")}</p> : null}{query.data ? <><h2 className="timeline-summary-title">{t("nightlySummary")}</h2><div className="timeline-summary">{tiles.map((tile) => <MetricTile key={tile.labelKey} tile={tile} days={days} />)}</div><DailyHeartRateChart days={days} syncedThrough={query.data.synced_through} /><div className="timeline-charts">{tiles.map((tile) => <NightlyChart key={tile.labelKey} tile={tile} days={days} syncedThrough={query.data.synced_through} domainStart={domainStart} />)}</div><TimelineEvents events={events} /><AddTimelineEvent defaultDate={query.data.end} onCreated={() => query.refetch()} /></> : null}</section>; }
