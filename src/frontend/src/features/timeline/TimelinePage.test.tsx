import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("echarts-for-react", () => ({ default: ({ option }: { option: { series: unknown } }) => <div data-testid="echarts" data-series={JSON.stringify(option.series)} /> }));

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
});
