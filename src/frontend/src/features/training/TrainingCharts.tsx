import ReactECharts from "echarts-for-react";
import { useEffect, useRef } from "react";

import { TrainingSeries } from "../../api/training";
import { categoryLineSeries } from "../../components/chartSeries";
import { useLanguage } from "../../i18n/useLanguage";
import { formatMetricTooltipValue } from "./trainingChartFormatting";

type MetricField = keyof Pick<TrainingSeries["buckets"][number], "total_distance_meters" | "average_heart_rate" | "average_pace_seconds_per_kilometer" | "average_duration_seconds" | "average_distance_pace_index">;

type Metric = {
  label: string;
  field: MetricField;
  value: (bucket: TrainingSeries["buckets"][number]) => number | null;
  format: (value: number) => string;
  axisFormat?: (value: number) => string;
};

function formatMinutesSeconds(seconds: number) {
  const roundedSeconds = Math.round(seconds);
  return `${Math.floor(roundedSeconds / 60)}:${String(roundedSeconds % 60).padStart(2, "0")}`;
}

function formatHoursMinutes(seconds: number) {
  const totalMinutes = Math.round(seconds / 60);
  return `${Math.floor(totalMinutes / 60)}:${String(totalMinutes % 60).padStart(2, "0")}`;
}

export function TrainingCharts({ series, color, onSelect }: { series: TrainingSeries; color: string; onSelect: (index: number) => void }) {
  const { t } = useLanguage();
  const chartRef = useRef<ReactECharts>(null);
  const labels = series.buckets.map((bucket) => bucket.date);
  const metrics: Metric[] = [
    { label: t("totalDistance"), field: "total_distance_meters", value: (bucket) => bucket.total_distance_meters === null ? null : bucket.total_distance_meters / 1000, format: (value) => t("kilometerValue", { value: value.toFixed(2) }) },
    { label: t("meanHeartRate"), field: "average_heart_rate", value: (bucket) => bucket.average_heart_rate, format: (value) => t("beatsPerMinuteValue", { value: Math.round(value) }) },
    { label: t("meanPace"), field: "average_pace_seconds_per_kilometer", value: (bucket) => bucket.average_pace_seconds_per_kilometer, format: (value) => t("paceValue", { value: formatMinutesSeconds(value) }), axisFormat: formatMinutesSeconds },
    { label: t("meanDuration"), field: "average_duration_seconds", value: (bucket) => bucket.average_duration_seconds, format: formatHoursMinutes, axisFormat: formatHoursMinutes },
    { label: t("distancePaceIndex"), field: "average_distance_pace_index", value: (bucket) => bucket.average_distance_pace_index, format: (value) => value.toFixed(3) },
  ];
  const axisNames = [t("totalDistanceAxis"), t("meanHeartRateAxis"), t("meanPaceAxis"), t("meanDurationAxis"), t("distancePaceIndex")];
  const syncedThroughIndex = series.synced_through === null ? null : series.buckets.reduce(
    (target, bucket, index) => bucket.date <= series.synced_through! ? index : target,
    -1,
  );
  useEffect(() => {
    const chart = chartRef.current?.getEchartsInstance();
    const renderer = chart?.getZr();
    const move = (event: { offsetX: number; offsetY: number }) => chart?.dispatchAction({ type: "updateAxisPointer", x: event.offsetX, y: event.offsetY });
    renderer?.on("mousemove", move);
    return () => { renderer?.off("mousemove", move); };
  }, []);
  return <div className="training-charts-frame">
    <div className="training-chart-borders" aria-hidden="true">
      {metrics.map((metric, index) => <span key={metric.field} style={{ top: 6 + index * 186 }} />)}
    </div>
    <ReactECharts ref={chartRef} className="training-charts" style={{ height: 936 }} option={{
    tooltip: { trigger: "axis", triggerOn: "mousemove", axisPointer: { show: true, type: "line", snap: false, label: { show: true } }, formatter: (items: Array<{ axisValue: string; seriesName: string; value: unknown }>) => `${items[0]?.axisValue ?? ""}<br/>${items.map((item) => `${item.seriesName}: ${formatMetricTooltipValue(item.value, metrics.find((metric) => metric.label === item.seriesName)?.format ?? String)}`).join("<br/>")}` },
    axisPointer: { link: [{ xAxisIndex: "all" }], snap: false, label: { show: true } },
    grid: metrics.map((_, index) => ({ left: 82, right: 32, top: 48 + index * 186, height: 90 })),
    xAxis: metrics.map((_, index) => ({ type: "category", data: labels, gridIndex: index, axisLabel: { show: true, hideOverlap: true }, axisPointer: { show: true, snap: false, triggerTooltip: true } })),
    yAxis: metrics.map((metric, index) => ({ type: "value", name: axisNames[index], gridIndex: index, scale: true, axisLabel: { formatter: (value: number) => metric.axisFormat ? metric.axisFormat(value) : String(Math.round(value * 100) / 100) } })),
    series: [
      ...metrics.flatMap((metric, index) => categoryLineSeries({
        idPrefix: metric.field,
        name: metric.label,
        values: series.buckets.map((bucket) => metric.value(bucket)),
        color,
        xAxisIndex: index,
        yAxisIndex: index,
        syncedThroughIndex: syncedThroughIndex === null || syncedThroughIndex < 0 ? null : syncedThroughIndex,
      })),
      ...metrics.map((metric, index) => { const anchor = series.buckets.map((bucket) => metric.value(bucket)).find((value) => value !== null) ?? 0; return { name: `__pointer-${index}`, type: "line", xAxisIndex: index, yAxisIndex: index, silent: true, showSymbol: false, lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, tooltip: { show: false }, data: series.buckets.map((bucket) => metric.value(bucket) ?? anchor) }; }),
    ],
  }} onEvents={{ click: (event: { dataIndex?: number }) => { if (event.dataIndex !== undefined) onSelect(event.dataIndex); } }} />
  </div>;
}
