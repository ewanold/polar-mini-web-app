import { lazy, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { TrainingRange, useTrainingGroups, useTrainingSeries } from "../../api/training";
import type { TranslationKey } from "../../i18n/language-context";
import { useLanguage } from "../../i18n/useLanguage";
import { BucketSessions } from "./BucketSessions";

const TrainingCharts = lazy(async () => ({ default: (await import("./TrainingCharts")).TrainingCharts }));

const ranges: { value: TrainingRange; label: TranslationKey }[] = [
  { value: "4w", label: "range4Weeks" }, { value: "6m", label: "range6Months" }, { value: "all", label: "rangeAll" },
];

const resolutionKeys = { day: "resolutionDaily", week: "resolutionWeekly", month: "resolutionMonthly" } as const;

function rangeFrom(value: string | null): TrainingRange {
  return value === "6m" || value === "all" ? value : "4w";
}

export function TrainingPage() {
  const { t } = useLanguage();
  const [params, setParams] = useSearchParams();
  const range = rangeFrom(params.get("range"));
  const requestedGroupId = Number(params.get("group"));
  const groupsQuery = useTrainingGroups();
  const groups = groupsQuery.data ?? [];
  const group = groups.find((item) => item.id === requestedGroupId) ?? groups[0];
  const seriesQuery = useTrainingSeries(group?.id ?? null, range);
  const [selectedBucket, setSelectedBucket] = useState<number | null>(null);

  useEffect(() => {
    if (group && group.id !== requestedGroupId) {
      setParams({ range, group: String(group.id) }, { replace: true });
    }
  }, [group, range, requestedGroupId, setParams]);

  function select(nextRange: TrainingRange, nextGroupId = group?.id) {
    const next = new URLSearchParams({ range: nextRange });
    if (nextGroupId) next.set("group", String(nextGroupId));
    setParams(next);
  }

  const series = seriesQuery.data;
  const rangeLabel = t(ranges.find((option) => option.value === range)?.label ?? "range4Weeks");
  return <section aria-labelledby="training-title" className="page-panel">
    <p className="eyebrow">{t("trainingAnalysis")}</p><h1 id="training-title">{t("trainingProgress")}</h1>
    <div aria-label={t("trainingRange")}>{ranges.map((option) => <button key={option.value} type="button" aria-pressed={range === option.value} onClick={() => select(option.value)}>{t(option.label)}</button>)}</div>
    {group ? <label>{t("trainingGroup")} <select aria-label={t("trainingGroup")} value={group.id} onChange={(event) => select(range, Number(event.target.value))}>{groups.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label> : null}
    {groupsQuery.isLoading ? <p>{t("loadingTrainingGroups")}</p> : null}
    {groupsQuery.isError ? <p role="alert">{t("unableToLoadTrainingGroups")}</p> : null}
    {!groupsQuery.isLoading && !groupsQuery.isError && groups.length === 0 ? <p>{t("createGroupToViewProgress")}</p> : null}
    {group ? <p>{t("showingProgress", { range: rangeLabel, group: group.name })}</p> : null}
    {seriesQuery.isLoading ? <p>{t("loadingTrainingProgress")}</p> : null}
    {seriesQuery.isError ? <p role="alert">{t("unableToLoadTrainingProgress")}</p> : null}
    {series && series.buckets.every((bucket) => bucket.session_count === 0) ? <p>{t("noMappedSessionsInRange")}</p> : null}
    {series && series.buckets.some((bucket) => bucket.session_count > 0) ? <p>{t("bucketsAvailable", { count: series.buckets.length, resolution: t(resolutionKeys[series.resolution]) })}</p> : null}
    {series && group && series.buckets.some((bucket) => bucket.session_count > 0) ? <Suspense fallback={<p>{t("loadingCharts")}</p>}><TrainingCharts series={series} color={group.color} onSelect={setSelectedBucket} /></Suspense> : null}
    {series && group && selectedBucket !== null && series.buckets[selectedBucket] ? <BucketSessions groupId={group.id} start={series.buckets[selectedBucket].date} end={series.buckets[selectedBucket].end_date} /> : null}
  </section>;
}
