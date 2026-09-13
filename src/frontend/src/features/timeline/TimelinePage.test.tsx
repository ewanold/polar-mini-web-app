import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("echarts-for-react", () => ({ default: ({ option }: { option: { series: unknown; xAxis: { min: string; axisLabel: { formatter: (value: number) => string } } } }) => <div data-testid="echarts" data-series={JSON.stringify(option.series)} data-x-axis-min={option.xAxis.min} data-x-axis-label={option.xAxis.axisLabel.formatter(Date.UTC(2026, 8, 1))} /> }));

import { LanguageProvider } from "../../i18n/LanguageProvider";
import { TimelinePage } from "./TimelinePage";

describe("TimelinePage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ start: "2026-09-01", end: "2026-09-01", days: [{ date: "2026-09-01", sleep: null, activity: null, heart_rate: { average: 65, minimum: 58, maximum: 72, samples: [{ sampled_at: "2026-09-01T08:00:00", heart_rate: 58 }, { sampled_at: "2026-09-01T20:00:00", heart_rate: 72 }] }, nightly_recharge: { heart_rate_avg: 59, heart_rate_variability_avg: 68, breathing_rate_avg: 13.4, ans_charge: null, nightly_recharge_status: null } }] }) }));
  });

  it("shows current nightly metric tiles, seven-day averages, and editable events", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ start: "2026-09-01", end: "2026-09-01", days: [{ date: "2026-09-01", sleep: null, activity: null, heart_rate: { average: 65, minimum: 58, maximum: 72, samples: [{ sampled_at: "2026-09-01T08:00:00", heart_rate: 58 }, { sampled_at: "2026-09-01T20:00:00", heart_rate: 72 }] }, nightly_recharge: { heart_rate_avg: 59, heart_rate_variability_avg: 68, breathing_rate_avg: 13.4, ans_charge: null, nightly_recharge_status: null }, events: [{ id: 4, date: "2026-09-01", description: "Late dinner" }] }] }) }));
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><LanguageProvider><TimelinePage /></LanguageProvider></QueryClientProvider>);
    expect(await screen.findByRole("heading", { name: "Last night" })).toBeVisible();
    expect(screen.getAllByText("HRV")).toHaveLength(2);
    expect(screen.getByText("68.0")).toBeVisible();
    expect(screen.getByText("7-day avg: 68.0 ms")).toBeVisible();
    expect(screen.getAllByText("ANS charge")).toHaveLength(2);
    expect(screen.getAllByText("Nightly Recharge")).toHaveLength(2);
    expect(screen.queryByText("HRV last night")).not.toBeInTheDocument();
    expect(screen.queryByText("Blood oxygen")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Daily heart rate" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "HRV" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Events" })).toBeVisible();
    expect(screen.getByText("Late dinner")).toBeVisible();
    expect(screen.getByRole("button", { name: "Edit event: Late dinner" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Delete event: Late dinner" })).toBeVisible();
    const dailyChartSeries = screen.getAllByTestId("echarts")[0].dataset.series ?? "";
    expect(dailyChartSeries).not.toContain("markPoint");
    expect(dailyChartSeries).toContain('"color":"#d97706"');
  });

  it("marks actual values, dots internal gaps, and carries the last value through a successful sync", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      start: "2026-09-01",
      end: "2026-09-04",
      synced_through: "2026-09-04",
      days: [
        { date: "2026-09-01", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: { heart_rate_avg: 60, heart_rate_variability_avg: null, breathing_rate_avg: null, ans_charge: null, nightly_recharge_status: null } },
        { date: "2026-09-02", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: null },
        { date: "2026-09-03", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: { heart_rate_avg: 64, heart_rate_variability_avg: null, breathing_rate_avg: null, ans_charge: null, nightly_recharge_status: null } },
        { date: "2026-09-04", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: null },
      ],
    }) }));
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><LanguageProvider><TimelinePage /></LanguageProvider></QueryClientProvider>);

    const chart = await screen.findByTestId("echarts");
    const chartSeries = JSON.parse(chart.dataset.series ?? "[]") as Array<{ id?: string; type?: string; symbol?: string; lineStyle?: { type?: string }; data?: unknown[] }>;
    expect(chartSeries).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "actual-points", type: "scatter", symbol: "circle", data: [["2026-09-01", 60], ["2026-09-03", 64]] }),
      expect.objectContaining({ id: "missing-gap-0", lineStyle: expect.objectContaining({ type: "dotted" }), data: [["2026-09-01", 60], ["2026-09-03", 64]] }),
      expect.objectContaining({ id: "carry-forward", lineStyle: expect.objectContaining({ type: "dotted" }), data: [["2026-09-03", 64], ["2026-09-04", 64]] }),
    ]));
  });

  it("uses one shared start date for every nightly chart", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      start: "2026-09-01",
      end: "2026-09-04",
      synced_through: "2026-09-04",
      days: [
        { date: "2026-09-01", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: { heart_rate_avg: 60, heart_rate_variability_avg: null, breathing_rate_avg: null, ans_charge: null, nightly_recharge_status: null } },
        { date: "2026-09-02", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: null },
        { date: "2026-09-03", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: { heart_rate_avg: 64, heart_rate_variability_avg: null, breathing_rate_avg: null, ans_charge: 2.5, nightly_recharge_status: null } },
        { date: "2026-09-04", sleep: null, activity: null, heart_rate: null, events: [], nightly_recharge: null },
      ],
    }) }));
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><LanguageProvider><TimelinePage /></LanguageProvider></QueryClientProvider>);

    const charts = await screen.findAllByTestId("echarts");
    expect(charts).toHaveLength(2);
    expect(charts.map((chart) => chart.dataset.xAxisMin)).toEqual(["2026-09-01", "2026-09-01"]);
    expect(charts.map((chart) => chart.dataset.xAxisLabel)).toEqual(["09-01", "09-01"]);
  });

  it("adds an event from the bottom form with an explicitly entered date", async () => {
    const timeline = { start: "2026-09-01", end: "2026-09-04", synced_through: "2026-09-04", days: [] };
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => ({
      ok: true,
      status: init?.method === "POST" ? 201 : 200,
      json: async () => init?.method === "POST" ? { id: 5, date: "2026-08-31", description: "Sore knee" } : timeline,
    } as Response));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><LanguageProvider><TimelinePage /></LanguageProvider></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: "Add event" }));
    await user.clear(screen.getByLabelText("Date"));
    await user.type(screen.getByLabelText("Date"), "2026-08-31");
    await user.type(screen.getByLabelText("Description"), "Sore knee");
    await user.click(screen.getByRole("button", { name: "Save event" }));

    expect(fetchMock).toHaveBeenCalledWith("/api/timeline/events", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ date: "2026-08-31", description: "Sore knee" }),
    }));
  });
});
