import ReactECharts from "echarts-for-react";

import { useTimeline, type TimelineDay, type TimelineEvent, type TimelineNightlyRecharge } from "../../api/timeline";
import { useLanguage } from "../../i18n/useLanguage";

type Metric = keyof TimelineNightlyRecharge;
type Tile = { labelKey: "nightlyHrv" | "nightlyHeartRate" | "respiration" | "ansCharge" | "categoryNightlyRecharge"; metric: Metric; unit: string; favourable: "higher" | "lower" };
const tiles: Tile[] = [
  { labelKey: "nightlyHrv", metric: "heart_rate_variability_avg", unit: "ms", favourable: "higher" },
  { labelKey: "nightlyHeartRate", metric: "heart_rate_avg", unit: "bpm", favourable: "lower" },
  { labelKey: "respiration", metric: "breathing_rate_avg", unit: "breaths/min", favourable: "lower" },
  { labelKey: "ansCharge", metric: "ans_charge", unit: "score", favourable: "higher" },
  { labelKey: "categoryNightlyRecharge", metric: "nightly_recharge_status", unit: "status", favourable: "higher" },
];

function mean(values: Array<number | null>) { const usable = values.filter((value): value is number => value !== null); return usable.length ? usable.reduce((sum, value) => sum + value, 0) / usable.length : null; }
function nightlyValues(days: TimelineDay[], metric: Metric) { return days.map((day) => day.nightly_recharge?.[metric] ?? null); }
function unitFor(tile: Tile, t: ReturnType<typeof useLanguage>["t"]) { return tile.unit === "breaths/min" ? t("breathsPerMinute") : tile.unit; }

function MetricTile({ tile, days }: { tile: Tile; days: TimelineDay[] }) {
  const { t } = useLanguage(); const unit = unitFor(tile, t); const values = nightlyValues(days, tile.metric); const current = [...values].reverse().find((value): value is number => value !== null) ?? null; const average = mean(values.slice(-7)); const change = current !== null && average !== null && average !== 0 ? (current / average - 1) * 100 : null; const favourable = change !== null && (tile.favourable === "higher" ? change >= 0 : change <= 0);
  return <article className="timeline-summary-tile"><p>{t(tile.labelKey)}</p><strong>{current === null ? "–" : current.toFixed(1)}<small>{unit}</small></strong><span>{t("sevenDayAverage", { value: average === null ? "–" : average.toFixed(1), unit })}</span>{change !== null ? <em className={favourable ? "positive" : "negative"}>{t("percentageVsAverage", { arrow: change >= 0 ? "▲" : "▼", value: Math.abs(change).toFixed(0) })}</em> : null}</article>;
}

function eventLineSeries(points: Array<[string, number]>, events: TimelineEvent[]) {
  const eventDates = new Set(events.map((event) => event.date));
  const groups: Array<{ data: Array<[string, number]>; eventDay: boolean }> = [];
  for (const point of points) {
    const eventDay = eventDates.has(point[0].slice(0, 10));
    const current = groups.at(-1);
    if (!current || current.eventDay !== eventDay) {
      groups.push({ data: current ? [current.data.at(-1)!, point] : [point], eventDay });
    } else {
      current.data.push(point);
    }
  }
  return groups.map((group) => ({
    type: "line" as const,
    data: group.data,
    showSymbol: false,
    lineStyle: { width: 1.5, color: group.eventDay ? "#d97706" : "#006f7b" },
    itemStyle: { color: group.eventDay ? "#d97706" : "#006f7b" },
  }));
}

function LineChart({ title, unit, points, events, className, rolling24Hours = false }: { title: string; unit: string; points: Array<[string, number]>; events: TimelineEvent[]; className: string; rolling24Hours?: boolean }) {
  const { t } = useLanguage();
  if (!points.length) return <section className={className}><h2>{title}</h2><p>{t("noPolarNightlyData")}</p></section>;
  const eventsFor = (value: string) => events.filter((event) => event.date === value.slice(0, 10)).map((event) => event.description).join("; ");
  const addEvent = async (value: string) => { const description = window.prompt(t("newEventPrompt", { date: value.slice(0, 10) })); if (!description?.trim()) return; await fetch("/api/timeline/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ date: value.slice(0, 10), description }) }); window.location.reload(); };
  const latest = points.at(-1)?.[0]; const initialStart = latest ? new Date(new Date(latest).getTime() - 86_400_000).toISOString() : undefined;
  return <section className={className}><h2>{title}</h2><ReactECharts style={{ height: 230 }} onEvents={{ dblclick: (params: { value?: [string, number] }) => { if (params.value?.[0]) void addEvent(params.value[0]); } }} option={{ animation: false, grid: { left: 52, right: 18, top: 20, bottom: rolling24Hours ? 62 : 40 }, dataZoom: rolling24Hours ? [{ type: "inside", startValue: initialStart, endValue: latest }, { type: "slider", startValue: initialStart, endValue: latest, height: 18, bottom: 12 }] : undefined, tooltip: { trigger: "axis", axisPointer: { type: "cross" }, formatter: (items: Array<{ axisValueLabel: string; value: [string, number] }>) => `${items[0]?.axisValueLabel}<br/>${items[0]?.value[1].toFixed(1)} ${unit}${eventsFor(items[0]?.value[0] ?? "") ? `<br/>${eventsFor(items[0]?.value[0] ?? "")}` : ""}` }, xAxis: { type: "time", axisLabel: { formatter: (value: number) => new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) } }, yAxis: { type: "value", name: unit, scale: true }, series: eventLineSeries(points, events) }} /></section>;
}

function TimelineEvents({ events }: { events: TimelineEvent[] }) {
  const { t } = useLanguage();
  const editEvent = async (event: TimelineEvent) => { const description = window.prompt(t("editEventPrompt", { date: event.date }), event.description); if (!description?.trim() || description.trim() === event.description) return; const response = await fetch(`/api/timeline/events/${event.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ description }) }); if (!response.ok) { window.alert(t("eventSaveFailed")); return; } window.location.reload(); };
  const deleteEvent = async (event: TimelineEvent) => { if (!window.confirm(t("deleteEventConfirm", { description: event.description }))) return; const response = await fetch(`/api/timeline/events/${event.id}`, { method: "DELETE" }); if (!response.ok) { window.alert(t("eventDeleteFailed")); return; } window.location.reload(); };
  if (!events.length) return null;
  return <section className="timeline-events"><h2>{t("events")}</h2><ul>{events.map((event) => <li key={event.id}><time dateTime={event.date}>{event.date}</time><span>{event.description}</span><button type="button" aria-label={t("editEvent", { description: event.description })} onClick={() => void editEvent(event)}>{t("edit")}</button><button className="danger-button" type="button" aria-label={t("deleteEvent", { description: event.description })} onClick={() => void deleteEvent(event)}>{t("delete")}</button></li>)}</ul></section>;
}

function NightlyChart({ tile, days }: { tile: Tile; days: TimelineDay[] }) { const { t } = useLanguage(); return <LineChart className="timeline-chart" title={t(tile.labelKey)} unit={unitFor(tile, t)} events={days.flatMap((day) => day.events ?? [])} points={days.flatMap((day) => { const value = day.nightly_recharge?.[tile.metric]; return value === null || value === undefined ? [] : [[day.date, value] as [string, number]]; })} />; }
function DailyHeartRateChart({ days }: { days: TimelineDay[] }) { const { t } = useLanguage(); const points = days.flatMap((day) => day.heart_rate?.samples ?? []).map((sample) => [sample.sampled_at, sample.heart_rate] as [string, number]); return <LineChart className="timeline-day-heart-rate" title={t("dailyHeartRate")} unit="bpm" events={days.flatMap((day) => day.events ?? [])} points={points} rolling24Hours />; }

export function TimelinePage() { const { t } = useLanguage(); const query = useTimeline(); const days = query.data?.days ?? []; const events = days.flatMap((day) => day.events ?? []); return <section aria-labelledby="timeline-title" className="page-panel"><p className="eyebrow">{t("dailyTimeline")}</p><h1 id="timeline-title">{t("dailyTimeline")}</h1>{query.isLoading ? <p>{t("timelineLoading")}</p> : null}{query.isError ? <p role="alert">{t("timelineError")}</p> : null}{query.data ? <><h2 className="timeline-summary-title">{t("nightlySummary")}</h2><div className="timeline-summary">{tiles.map((tile) => <MetricTile key={tile.labelKey} tile={tile} days={days} />)}</div><DailyHeartRateChart days={days} /><div className="timeline-charts">{tiles.map((tile) => <NightlyChart key={tile.labelKey} tile={tile} days={days} />)}</div><TimelineEvents events={events} /></> : null}</section>; }
