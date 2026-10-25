import ReactECharts from "echarts-for-react";

import { type CardioLoadSeries, type TrainingRange, useCardioLoad } from "../../api/training";
import { timeLineSeries } from "../../components/chartSeries";
import { useLanguage } from "../../i18n/useLanguage";

function compactLocalDate(value: number) { const date = new Date(value); return `${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }

export function CardioLoadPlot({ days, start, end, syncedThrough }: { days: CardioLoadSeries["days"]; start: string; end: string; syncedThrough: string | null }) {
  const { t } = useLanguage();
  const components = [
    { metric: "strain" as const, name: t("cardioStrain"), color: "#d97706" },
    { metric: "tolerance" as const, name: t("cardioTolerance"), color: "#006f7b" },
  ];
  const series = components.flatMap(({ metric, name, color }) => {
    const points = days.flatMap((day): Array<[string, number]> => {
      const value = day.cardio_load?.[metric];
      return typeof value === "number" ? [[day.date, value]] : [];
    });
    return timeLineSeries({ points, color, gapThresholdMs: 36 * 60 * 60 * 1000, syncedThrough, colorForDate: () => color })
      .map((series) => ({ ...series, id: `${metric}-${series.id}`, ...(series.type === "scatter" ? { name } : {}) }));
  });
  const hasData = days.some((day) => day.cardio_load?.strain != null || day.cardio_load?.tolerance != null);
  return <section className="timeline-chart timeline-cardio-load" aria-labelledby="cardio-load-title">
    <h2 id="cardio-load-title">{t("cardioLoad")}</h2>
    <p>{t("cardioLoadDescription")}</p>
    {hasData ? <ReactECharts style={{ height: 280 }} option={{
      animation: false,
      grid: { left: 52, right: 18, top: 45, bottom: 40 },
      legend: { data: components.map(({ name }) => name), top: 0, selectedMode: false },
      tooltip: { trigger: "axis", axisPointer: { type: "cross" }, valueFormatter: (value: number) => typeof value === "number" ? value.toFixed(1) : "–" },
      xAxis: { type: "time", min: start, max: end, axisLabel: { hideOverlap: true, formatter: compactLocalDate } },
      yAxis: { type: "value", name: "TRIMP", min: 0 },
      series,
    }} /> : <p>{t("noCardioLoad")}</p>}
  </section>;
}

export function CardioLoadChart({ range }: { range: TrainingRange }) {
  const { t } = useLanguage();
  const query = useCardioLoad(range);
  if (query.isLoading) return <p>{t("loadingTrainingProgress")}</p>;
  if (query.isError) return <p role="alert">{t("unableToLoadTrainingProgress")}</p>;
  return query.data ? <CardioLoadPlot days={query.data.days} start={query.data.start} end={query.data.end} syncedThrough={query.data.synced_through} /> : null;
}
