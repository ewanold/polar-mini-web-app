import { useBucketSessions } from "../../api/training";
import { useLanguage } from "../../i18n/useLanguage";

export function BucketSessions({ groupId, start, end }: { groupId: number; start: string; end: string }) {
  const { t } = useLanguage();
  const query = useBucketSessions(groupId, start, end);
  if (query.isLoading) return <p>{t("loadingContributingSessions")}</p>;
  if (query.isError) return <p role="alert">{t("unableToLoadContributingSessions")}</p>;
  if (!query.data?.length) return <p>{t("noContributingSessions")}</p>;
  return <table aria-label={t("contributingSessions")}><thead><tr><th>{t("date")}</th><th>{t("polarType")}</th><th>{t("duration")}</th><th>{t("pace")}</th><th>{t("heartRate")}</th><th>{t("index")}</th></tr></thead><tbody>{query.data.map((session) => <tr key={session.external_id}><td>{session.local_date}</td><td>{session.sport_type}</td><td>{session.duration_seconds === null ? "-" : t("minuteValue", { value: Math.round(session.duration_seconds / 60) })}</td><td>{session.average_pace_seconds_per_kilometer === null ? "-" : t("paceValue", { value: `${Math.floor(session.average_pace_seconds_per_kilometer / 60)}:${String(Math.round(session.average_pace_seconds_per_kilometer % 60)).padStart(2, "0")}` })}</td><td>{session.average_heart_rate ?? "-"}</td><td>{session.duration_pace_index?.toFixed(2) ?? "-"}</td></tr>)}</tbody></table>;
}
