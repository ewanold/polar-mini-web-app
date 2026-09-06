import { FormEvent, useEffect, useState } from "react";

import type { TranslationKey } from "../../i18n/language-context";
import { useLanguage } from "../../i18n/useLanguage";

type TrainingGroup = {
  id: number;
  name: string;
  slug: string;
  color: string;
  position: number;
  enabled: boolean;
};

type MappingState = "mapped" | "unmapped" | "ignored";

type DeleteDisposition = "unmapped" | "reassign";

type SportTypeMapping = {
  sport_type: string;
  session_count: number;
  state: MappingState;
  group_id: number | null;
};

function slugify(name: string) {
  return name.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export function MappingsPage() {
  const { t } = useLanguage();
  const [groups, setGroups] = useState<TrainingGroup[]>([]);
  const [sportTypes, setSportTypes] = useState<SportTypeMapping[]>([]);
  const [name, setName] = useState("");
  const [groupToDelete, setGroupToDelete] = useState<TrainingGroup | null>(null);
  const [replacementGroupId, setReplacementGroupId] = useState<number | null>(null);
  const [error, setError] = useState<{ key: TranslationKey; values?: Record<string, string | number> } | null>(null);

  useEffect(() => {
    void Promise.all([fetch("/api/training/groups"), fetch("/api/training/sport-types")])
      .then(async ([groupsResponse, sportTypesResponse]) => {
        if (!groupsResponse.ok || !sportTypesResponse.ok) {
          throw new Error();
        }
        const [loadedGroups, loadedSportTypes] = await Promise.all([
          groupsResponse.json() as Promise<TrainingGroup[]>,
          sportTypesResponse.json() as Promise<SportTypeMapping[]>,
        ]);
        setGroups(loadedGroups);
        setSportTypes(loadedSportTypes);
      })
      .catch(() => setError({ key: "unableToLoadMappings" }));
  }, []);

  async function createGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;
    setError(null);
    const response = await fetch("/api/training/groups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: trimmedName, slug: slugify(trimmedName), color: "#006f7b" }),
    });
    if (!response.ok) {
      setError({ key: "unableToCreateGroup" });
      return;
    }
    const group = (await response.json()) as TrainingGroup;
    setGroups((current) => [...current, group]);
    setName("");
  }

  function selectionFor(mapping: SportTypeMapping) {
    if (mapping.state === "mapped" && mapping.group_id !== null) {
      return `group:${mapping.group_id}`;
    }
    return mapping.state;
  }

  async function updateMapping(mapping: SportTypeMapping, selection: string) {
    const payload = selection.startsWith("group:")
      ? { state: "mapped" as const, group_id: Number(selection.slice("group:".length)) }
      : { state: selection as Exclude<MappingState, "mapped">, group_id: null };
    setError(null);
    const response = await fetch(`/api/training/sport-types/${encodeURIComponent(mapping.sport_type)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setError({ key: "unableToUpdateSportType", values: { sportType: mapping.sport_type } });
      return;
    }
    const updated = (await response.json()) as SportTypeMapping;
    setSportTypes((current) =>
      current.map((entry) => (entry.sport_type === updated.sport_type ? updated : entry)),
    );
  }

  function openDeleteDialog(group: TrainingGroup) {
    setGroupToDelete(group);
    setReplacementGroupId(groups.find((candidate) => candidate.id !== group.id)?.id ?? null);
  }

  async function deleteGroup(
    group: TrainingGroup,
    disposition: DeleteDisposition,
    replacementId: number | null = null,
  ) {
    setError(null);
    const response = await fetch(`/api/training/groups/${group.id}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        disposition === "reassign"
          ? { disposition, replacement_group_id: replacementId }
          : { disposition },
      ),
    });
    if (!response.ok) {
      setError({ key: "unableToDeleteGroup" });
      return;
    }
    setGroups((current) => current.filter((entry) => entry.id !== group.id));
    setSportTypes((current) => current.map((mapping) => {
      if (mapping.group_id !== group.id) return mapping;
      return replacementId === null
        ? { ...mapping, state: "unmapped", group_id: null }
        : { ...mapping, state: "mapped", group_id: replacementId };
    }));
    setGroupToDelete(null);
  }

  const unmappedSessionCount = sportTypes
    .filter((mapping) => mapping.state === "unmapped")
    .reduce((total, mapping) => total + mapping.session_count, 0);

  return (
    <section aria-labelledby="mappings-title" className="page-panel">
      <p className="eyebrow">{t("trainingSetup")}</p>
      <h1 id="mappings-title">{t("mappingsTitle")}</h1>
      <p>{t("mappingsDescription")}</p>
      {error ? <p role="alert">{t(error.key, error.values)}</p> : null}
      <form onSubmit={(event) => void createGroup(event)}>
        <label htmlFor="training-group-name">{t("groupName")}</label>
        <input id="training-group-name" value={name} onChange={(event) => setName(event.target.value)} />
        <button type="submit">{t("createGroup")}</button>
      </form>
      {groups.length === 0 ? <p>{t("noTrainingGroups")}</p> : null}
      <ul aria-label={t("trainingGroups")}>
        {groups.map((group) => (
          <li key={group.id}>
            {group.name} <button type="button" onClick={() => openDeleteDialog(group)}>{t("deleteGroup", { group: group.name })}</button>
          </li>
        ))}
      </ul>
      {groupToDelete ? (
        <div role="dialog" aria-modal="true" aria-labelledby="delete-group-dialog-title" className="mapping-delete-dialog">
          <h2 id="delete-group-dialog-title">{t("deleteGroupDialog", { group: groupToDelete.name })}</h2>
          <p>{t("deleteGroupWarning")}</p>
          <button type="button" onClick={() => void deleteGroup(groupToDelete, "unmapped")}>{t("unmapAndDelete")}</button>
          {replacementGroupId !== null ? (
            <form onSubmit={(event) => {
              event.preventDefault();
              void deleteGroup(groupToDelete, "reassign", replacementGroupId);
            }}>
              <label htmlFor="replacement-training-group">{t("reassignMappedTypesTo")}</label>
              <select
                id="replacement-training-group"
                value={replacementGroupId}
                onChange={(event) => setReplacementGroupId(Number(event.target.value))}
              >
                {groups.filter((group) => group.id !== groupToDelete.id).map((group) => (
                  <option key={group.id} value={group.id}>{group.name}</option>
                ))}
              </select>
              <button type="submit">{t("reassignAndDelete")}</button>
            </form>
          ) : null}
          <button type="button" onClick={() => setGroupToDelete(null)}>{t("cancel")}</button>
        </div>
      ) : null}
      <section className="mapping-section" aria-labelledby="observed-sport-types-title">
        <div>
          <h2 id="observed-sport-types-title">{t("observedSportTypes")}</h2>
          {unmappedSessionCount > 0 ? (
            <p className="mapping-warning" role="status">
              {t(unmappedSessionCount === 1 ? "oneUnassignedSession" : "unassignedSessions", { count: unmappedSessionCount })}
            </p>
          ) : null}
        </div>
        {sportTypes.length === 0 ? <p>{t("noImportedSessions")}</p> : null}
        {sportTypes.length > 0 ? (
          <div className="mapping-table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">{t("polarType")}</th>
                  <th scope="col">{t("sessions")}</th>
                  <th scope="col">{t("assignment")}</th>
                </tr>
              </thead>
              <tbody>
                {sportTypes.map((mapping) => (
                  <tr key={mapping.sport_type}>
                    <th scope="row">{mapping.sport_type}</th>
                    <td>{mapping.session_count}</td>
                    <td>
                      <label className="sr-only" htmlFor={`mapping-${mapping.sport_type}`}>{t("assignSportType", { sportType: mapping.sport_type })}</label>
                      <select
                        id={`mapping-${mapping.sport_type}`}
                        value={selectionFor(mapping)}
                        onChange={(event) => void updateMapping(mapping, event.target.value)}
                      >
                        <option value="unmapped">{t("unmapped")}</option>
                        <option value="ignored">{t("ignored")}</option>
                        {groups.map((group) => <option key={group.id} value={`group:${group.id}`}>{group.name}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
