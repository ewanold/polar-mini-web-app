import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("echarts-for-react", () => ({
  default: ({ option }: { option: { series: unknown } }) => <div data-testid="echarts" data-series={JSON.stringify(option.series)} />,
}));

import type { TrainingSeries } from "../../api/training";
import { LanguageProvider } from "../../i18n/LanguageProvider";
import { TrainingCharts } from "./TrainingCharts";

describe("TrainingCharts", () => {
  it("marks actual values, dots internal gaps, and carries the last value through a successful sync", () => {
    const bucket = (date: string, heartRate: number | null) => ({
      date,
      end_date: date,
      session_count: heartRate === null ? 0 : 1,
      total_distance_meters: null,
      average_heart_rate: heartRate,
      average_pace_seconds_per_kilometer: null,
      average_duration_seconds: null,
      average_duration_pace_index: null,
      average_heart_rate_sample_count: heartRate === null ? 0 : 1,
      average_pace_sample_count: 0,
      average_duration_sample_count: 0,
      average_duration_pace_index_sample_count: 0,
    });
    const series = {
      group: { id: 1, name: "Running", color: "#006f7b" },
      range: "4w",
      resolution: "day",
      timezone: "Europe/Berlin",
      aggregation_method: "arithmetic_mean_per_session",
      synced_through: "2026-09-04",
      buckets: [bucket("2026-09-01", 140), bucket("2026-09-02", null), bucket("2026-09-03", 145), bucket("2026-09-04", null)],
    } as TrainingSeries;

    render(<LanguageProvider><TrainingCharts series={series} color="#006f7b" onSelect={vi.fn()} /></LanguageProvider>);

    const chartSeries = JSON.parse(screen.getByTestId("echarts").dataset.series ?? "[]") as Array<{ id?: string; type?: string; symbol?: string; lineStyle?: { type?: string }; data?: unknown[] }>;
    expect(chartSeries).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "average_heart_rate-actual-points", type: "scatter", symbol: "circle", data: [140, null, 145, null] }),
      expect.objectContaining({ id: "average_heart_rate-missing-gap-0", lineStyle: expect.objectContaining({ type: "dotted" }), data: [140, null, 145, null] }),
      expect.objectContaining({ id: "average_heart_rate-carry-forward", lineStyle: expect.objectContaining({ type: "dotted" }), data: [null, null, 145, 145] }),
    ]));
  });
});