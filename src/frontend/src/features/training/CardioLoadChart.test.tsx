import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

vi.mock("echarts-for-react", () => ({ default: ({ option }: { option: { series: unknown } }) => <div data-testid="echarts" data-series={JSON.stringify(option.series)} /> }));

import { LanguageProvider } from "../../i18n/LanguageProvider";
import { CardioLoadPlot } from "./CardioLoadChart";

it("plots both cardio load components with zero values and dotted gaps", () => {
  render(<LanguageProvider><CardioLoadPlot start="2026-09-01" end="2026-09-04" syncedThrough="2026-09-04" days={[
    { date: "2026-09-01", cardio_load: { strain: 0, tolerance: 30 } },
    { date: "2026-09-03", cardio_load: { strain: 20, tolerance: null } },
  ]} /></LanguageProvider>);
  expect(screen.getByRole("heading", { name: "Cardio load" })).toBeVisible();
  const series = JSON.parse(screen.getByTestId("echarts").dataset.series ?? "[]");
  expect(series).toEqual(expect.arrayContaining([
    expect.objectContaining({ id: "strain-actual-points", name: "Strain (7 days)", data: [["2026-09-01", 0], ["2026-09-03", 20]] }),
    expect.objectContaining({ id: "tolerance-actual-points", name: "Tolerance (28 days)", data: [["2026-09-01", 30]] }),
    expect.objectContaining({ id: "strain-missing-gap-0" }),
    expect.objectContaining({ id: "strain-carry-forward" }),
  ]));
});
