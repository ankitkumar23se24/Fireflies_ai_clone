import { useQuery } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';

export interface AnalyticsOverview {
  total_meetings: number;
  total_seconds: number;
  average_seconds: number;
  meetings_this_week: number;
  meetings_this_month: number;
  action_items_total: number;
  action_items_completed: number;
  completion_rate: number;
  meetings_per_week: Array<{ week: string; meetings: number }>;
  duration_trend: Array<{ date: string; title: string; minutes: number }>;
  action_item_status: Array<{ status: string; count: number }>;
}

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => apiFetch<AnalyticsOverview>('/analytics/overview'),
  });
}
