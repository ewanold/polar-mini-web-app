import ReactECharts from "echarts-for-react";
import { useEffect, useRef } from "react";

import { TrainingSeries } from "../../api/training";
import { useLanguage } from "../../i18n/useLanguage";
import { formatMetricTooltipValue } from "./trainingChartFormatting";

type Metric = {
  label: string;
  field: keyof Pick<TrainingSeries["buckets"][number], "total_distance_meters" | "average_heart_rate" | "average_pace_seconds_per_kilometer" | "average_duration_seconds" | "average_duration_pace_index">;
  format: (value: number) => string;
};

function paceNumber(value: number) {
  return `${Math.floor(value / 60)}:${String(Math.round(value % 60)).padStart(2, "0")}`;
}

export function TrainingCharts({ series, color, onSelect }: { series: TrainingSeries; color: string; onSelect: (index: number) => void }) {
  const { t } = useLanguage();
  const chartRef = useRef<ReactECharts>(null);
  const labels = series.buckets.map((bucket) => bucket.date);
  const metrics: Metric[] = [
    { label: t("totalDistance"), field: "total_distance_meters", format: (value) => t("kilometerValue", { value: (value / 1000).toFixed(2) }) },
    { label: t("meanHeartRate"), field: "average_heart_rate", format: (value) => t("beatsPerMinuteValue", { value: Math.round(value) }) },
    { label: t("meanPace"), field: "average_pace_seconds_per_kilometer", format: (value) => t("paceValue", { value: paceNumber(value) }) },
    { label: t("meanDuration"), field: "average_duration_seconds", format: (value) => t("minuteValue", { value: Math.round(value / 60) }) },
    { label: t("durationPaceIndex"), field: "average_duration_pace_index", format: (value) => value.toFixed(2) },
  ];
  const axisNames = [t("totalDistanceAxis"), t("meanHeartRateAxis"), t("meanPaceAxis"), t("meanDurationAxis"), t("durationPaceIndex")];
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
    yAxis: metrics.map((_, index) => ({ type: "value", name: axisNames[index], gridIndex: index, scale: true, axisLabel: { formatter: (value: number) => String(Math.round(value * 100) / 100) } })),
    series: [
      ...metrics.map((metric, index) => ({ name: metric.label, type: "line", xAxisIndex: index, yAxisIndex: index, connectNulls: false, showSymbol: true, symbolSize: 7, lineStyle: { color }, itemStyle: { color }, data: series.buckets.map((bucket) => bucket[metric.field]) })),
      ...metrics.map((metric, index) => { const anchor = series.buckets.find((bucket) => bucket[metric.field] !== null)?.[metric.field] ?? 0; return { name: `__pointer-${index}`, type: "line", xAxisIndex: index, yAxisIndex: index, silent: true, showSymbol: false, lineStyle: { opacity: 0 }, itemStyle: { opacity: 0 }, tooltip: { show: false }, data: series.buckets.map((bucket) => bucket[metric.field] ?? anchor) }; }),
    ],
  }} onEvents={{ click: (event: { dataIndex?: number }) => { if (event.dataIndex !== undefined) onSelect(event.dataIndex); } }} />
  </div>;
}
