import { useEffect, useState } from "react";

import type { Translate, TranslationKey } from "../../i18n/language-context";
import { useLanguage } from "../../i18n/useLanguage";

type PolarStatus = {
  connected: boolean;
  polar_user_id: string | null;
  expires_at: string | null;
};

type SyncCategoryResult = {
  errors?: number;
  inserted?: number;
  imported?: number;
  skipped?: number;
  updated?: number;
  error?: string;
  error_samples?: string[];
};

type SyncResult = {
  connected: boolean;
  categories: Record<string, SyncCategoryResult>;
};

const categoryKeys: Partial<Record<string, TranslationKey>> = {
  activity: "categoryActivity",
  continuous_heart_rate: "categoryContinuousHeartRate",
  nightly_recharge: "categoryNightlyRecharge",
  sleep: "categorySleep",
  training: "categoryTraining",
};

function categoryLabel(category: string, t: Translate) {
  const key = categoryKeys[category];
  return key ? t(key) : category.replaceAll("_", " ").replace(/^./, (character) => character.toUpperCase());
}

export function SettingsPage() {
  const { t } = useLanguage();
  const [status, setStatus] = useState<PolarStatus | null>(null);
  const [error, setError] = useState<TranslationKey | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    void fetch("/api/polar/status")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error();
        }
        return (await response.json()) as PolarStatus;
      })
      .then(setStatus)
      .catch(() => {
        setError("unableToLoadPolarStatus");
      });
  }, []);

  async function syncNow() {
    setError(null);
    setSyncResult(null);
    setSyncing(true);
    try {
      const response = await fetch("/api/polar/sync", { method: "POST" });
      if (!response.ok) {
        throw new Error();
      }
      setSyncResult((await response.json()) as SyncResult);
    } catch {
      setError("polarSynchronizationFailed");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <section aria-labelledby="settings-title" className="page-panel">
      <p className="eyebrow">{t("polarConnection")}</p>
      <h1 id="settings-title">{t("settingsTitle")}</h1>
      {error ? <p role="alert">{t(error)}</p> : null}
      {status === null && !error ? <p>{t("checkingPolarConnection")}</p> : null}
      {status?.connected ? (
        <>
          <p>{t("connectedAsUser", { userId: status.polar_user_id ?? "-" })}</p>
          <button type="button" onClick={() => void syncNow()} disabled={syncing}>
            {t(syncing ? "synchronizing" : "syncNow")}
          </button>
        </>
      ) : null}
      {status && !status.connected ? <p>{t("notConnected")}</p> : null}
      {status && !status.connected ? (
        <a className="button-link" href="/api/polar/connect">
          {t("connectPolar")}
        </a>
      ) : null}
      {syncResult ? <p>{t("synchronizationCompleted")}</p> : null}
      {syncResult
        ? Object.entries(syncResult.categories).map(([category, result]) => (
            <p key={category}>
              {categoryLabel(category, t)}: {result.error ?? t("syncCategoryResult", { inserted: result.inserted ?? result.imported ?? 0, updated: result.updated ?? 0, skipped: result.skipped ?? 0, errors: result.errors ?? 0 })}
              {result.error_samples?.map((sample) => <span key={sample}> {sample}</span>)}
            </p>
          ))
        : null}
    </section>
  );
}
