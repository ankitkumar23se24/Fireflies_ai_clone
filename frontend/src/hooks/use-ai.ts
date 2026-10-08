import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';
import type { Meeting } from '@/types/meeting';

interface AskResponse {
  answer: string;
  citations: Array<{ segment_id: number; timestamp: number; speaker: string; text: string }>;
  provider: string;
}

export function useGenerateSummary(meetingId: number | string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiFetch<Meeting>(`/meetings/${meetingId}/generate-summary`, { method: 'POST' }),
    onSuccess: (meeting) => {
      queryClient.setQueryData(['meeting', meetingId], meeting);
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
  });
}

export function useAskMeeting(meetingId: number | string) {
  return useMutation({
    mutationFn: (question: string) =>
      apiFetch<AskResponse>(`/meetings/${meetingId}/ask`, {
        method: 'POST',
        body: JSON.stringify({ question }),
      }),
  });
}
