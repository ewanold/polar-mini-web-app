import { describe, expect, it } from "vitest";

import { formatMetricTooltipValue } from "./trainingChartFormatting";

describe("formatMetricTooltipValue", () => {
  it("renders ECharts missing-value markers without invoking the numeric formatter", () => {
    const numericFormatter = (value: number) => value.toFixed(2);

    expect(formatMetricTooltipValue("-", numericFormatter)).toBe("-");
    expect(formatMetricTooltipValue(null, numericFormatter)).toBe("-");
    expect(formatMetricTooltipValue(undefined, numericFormatter)).toBe("-");
  });

  it("formats finite numeric tooltip values", () => {
    expect(formatMetricTooltipValue(5, (value) => value.toFixed(2))).toBe("5.00");
  });
});
