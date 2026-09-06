import { useQuery } from "@tanstack/react-query";

export type TimelineNightlyRecharge = {
  heart_rate_avg: number | null;
  heart_rate_variability_avg: number | null;
  breathing_rate_avg: number | null;
  ans_charge: number | null;
  nightly_recharge_status: number | null;
};
export type TimelineHeartRate = {
  average: number; minimum: number; maximum: number;
  samples: { sampled_at: string; heart_rate: number }[];
};
export type TimelineEvent = { id: number; date: string; description: string };
export type TimelineDay = {
  date: string;
  sleep: { duration_seconds: number | null; score: number | null } | null;
  activity: { active_steps: number | null; active_calories: number | null } | null;
  nightly_recharge: TimelineNightlyRecharge | null;
  heart_rate: TimelineHeartRate | null;
  events: TimelineEvent[];
};
export type Timeline = { start: string; end: string; days: TimelineDay[] };

export function useTimeline() {
  return useQuery({
    queryKey: ["timeline"],
    queryFn: async () => {
      const response = await fetch("/api/timeline");
      if (!response.ok) throw new Error("Unable to load daily activity.");
      return response.json() as Promise<Timeline>;
    },
  });
}
