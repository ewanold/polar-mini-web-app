type CategorySeriesOptions = {
  idPrefix: string;
  name: string;
  values: Array<number | null>;
  color: string;
  xAxisIndex: number;
  yAxisIndex: number;
  syncedThroughIndex: number | null;
};

type TimeSeriesOptions = {
  points: Array<[string, number]>;
  color: string;
  gapThresholdMs: number;
  syncedThrough: string | null;
  colorForDate: (value: string) => string;
};

function lineData(values: Array<number | null>, first: number, second: number) {
  return values.map((value, index) => index === first || index === second ? value : null);
}

export function categoryLineSeries({
  idPrefix,
  name,
  values,
  color,
  xAxisIndex,
  yAxisIndex,
  syncedThroughIndex,
}: CategorySeriesOptions) {
  const common = { xAxisIndex, yAxisIndex };
  const actualIndexes = values.flatMap((value, index) => value === null ? [] : [index]);
  const gaps = actualIndexes.slice(1).flatMap((index, gapIndex) => {
    const previous = actualIndexes[gapIndex];
    if (index - previous <= 1) return [];
    return [{
      ...common,
      id: `${idPrefix}-missing-gap-${gapIndex}`,
      type: "line" as const,
      data: lineData(values, previous, index),
      connectNulls: true,
      showSymbol: false,
      silent: true,
      lineStyle: { color, type: "dotted" as const, width: 2 },
      tooltip: { show: false },
    }];
  });
  const lastActualIndex = actualIndexes.at(-1);
  const carryTarget = syncedThroughIndex === null ? null : Math.min(syncedThroughIndex, values.length - 1);
  const carry = lastActualIndex !== undefined && carryTarget !== null && carryTarget > lastActualIndex
    ? [{
        ...common,
        id: `${idPrefix}-carry-forward`,
        type: "line" as const,
        data: values.map((_, index) => index === lastActualIndex || index === carryTarget ? values[lastActualIndex] : null),
        connectNulls: true,
        showSymbol: false,
        silent: true,
        lineStyle: { color, type: "dotted" as const, width: 2 },
        tooltip: { show: false },
      }]
    : [];
  return [
    {
      ...common,
      id: `${idPrefix}-solid`,
      type: "line" as const,
      data: values,
      connectNulls: false,
      showSymbol: false,
      silent: true,
      lineStyle: { color, width: 2 },
      tooltip: { show: false },
    },
    ...gaps,
    ...carry,
    {
      ...common,
      id: `${idPrefix}-actual-points`,
      name,
      type: "scatter" as const,
      data: values,
      symbol: "circle",
      symbolSize: 7,
      itemStyle: { color },
      z: 5,
    },
  ];
}

export function timeLineSeries({
  points,
  color,
  gapThresholdMs,
  syncedThrough,
  colorForDate,
}: TimeSeriesOptions) {
  const segments = points.slice(1).map((point, index) => {
    const previous = points[index];
    const missing = new Date(point[0]).getTime() - new Date(previous[0]).getTime() > gapThresholdMs;
    return {
      id: missing ? `missing-gap-${index}` : `solid-segment-${index}`,
      type: "line" as const,
      data: [previous, point],
      showSymbol: false,
      silent: true,
      lineStyle: {
        width: 2,
        color: missing ? color : colorForDate(point[0]),
        ...(missing ? { type: "dotted" as const } : {}),
      },
      tooltip: { show: false },
    };
  });
  const last = points.at(-1);
  const carry = last && syncedThrough && new Date(syncedThrough).getTime() > new Date(last[0]).getTime()
    ? [{
        id: "carry-forward",
        type: "line" as const,
        data: [last, [syncedThrough, last[1]] as [string, number]],
        showSymbol: false,
        silent: true,
        lineStyle: { width: 2, color, type: "dotted" as const },
        tooltip: { show: false },
      }]
    : [];
  return [
    ...segments,
    ...carry,
    {
      id: "actual-points",
      type: "scatter" as const,
      data: points,
      symbol: "circle",
      symbolSize: 7,
      itemStyle: { color },
      z: 5,
    },
  ];
}
