export function formatMetricTooltipValue(
  value: unknown,
  numericFormatter: (value: number) => string,
): string {
  return typeof value === "number" && Number.isFinite(value) ? numericFormatter(value) : "-";
}
