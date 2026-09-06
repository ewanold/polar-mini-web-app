import { useQuery } from "@tanstack/react-query";

export type TrainingGroup = { id: number; name: string; color: string };
export type TrainingRange = "4w" | "6m" | "all";
export type TrainingBucket = {
  date: string; end_date: string; session_count: number;
  total_distance_meters: number | null;
  average_heart_rate: number | null; average_pace_seconds_per_kilometer: number | null;
  average_duration_seconds: number | null; average_duration_pace_index: number | null;
  average_heart_rate_sample_count: number; average_pace_sample_count: number;
  average_duration_sample_count: number; average_duration_pace_index_sample_count: number;
};
export type TrainingSeries = { group: TrainingGroup; range: TrainingRange; resolution: "day" | "week" | "month"; timezone: string; aggregation_method: "arithmetic_mean_per_session"; buckets: TrainingBucket[] };
export type TrainingSession = { external_id: string; local_date: string; sport_type: string; duration_seconds: number | null; average_heart_rate: number | null; average_pace_seconds_per_kilometer: number | null; duration_pace_index: number | null };

async function request<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error("Unable to load training progress.");
  return response.json() as Promise<T>;
}

export function useTrainingGroups() {
  return useQuery({ queryKey: ["training-groups"], queryFn: () => request<TrainingGroup[]>("/api/training/groups") });
}

export function useTrainingSeries(groupId: number | null, range: TrainingRange) {
  return useQuery({ queryKey: ["training-series", groupId, range], queryFn: () => request<TrainingSeries>(`/api/training/groups/${groupId}/series?range=${range}`), enabled: groupId !== null });
}

export function useBucketSessions(groupId: number | null, start: string | null, end: string | null) {
  return useQuery({ queryKey: ["training-bucket-sessions", groupId, start, end], queryFn: () => request<TrainingSession[]>(`/api/training/groups/${groupId}/sessions?start=${start}&end=${end}`), enabled: groupId !== null && start !== null && end !== null });
}
