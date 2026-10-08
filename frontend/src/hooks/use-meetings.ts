import { useQuery } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';
import type { Meeting, MeetingPageResponse } from '@/types/meeting';

export function useMeetings(q = '', page = 1, pageSize = 12) {
  return useQuery({
    queryKey: ['meetings', { q, page, pageSize }],
    queryFn: () => apiFetch<MeetingPageResponse>(`/meetings?q=${encodeURIComponent(q)}&page=${page}&page_size=${pageSize}`),
  });
}

export function useMeeting(meetingId: number | string | undefined) {
  return useQuery({
    queryKey: ['meeting', meetingId],
    queryFn: () => apiFetch<Meeting>(`/meetings/${meetingId}`),
    enabled: !!meetingId,
  });
}
