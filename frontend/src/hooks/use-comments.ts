import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';

export function useComments(meetingId: number | string | undefined) {
  return useQuery({
    queryKey: ['comments', meetingId],
    queryFn: () => apiFetch<Array<{ id: number; text: string; transcript_segment_id: number; created_at: string }>>(`/meetings/${meetingId}/comments`),
    enabled: !!meetingId,
  });
}

export function useHighlights(meetingId: number | string | undefined) {
  return useQuery({
    queryKey: ['highlights', meetingId],
    queryFn: () => apiFetch<Array<{ id: number; note: string; color: string; transcript_segment_id: number }>>(`/meetings/${meetingId}/highlights`),
    enabled: !!meetingId,
  });
}

export function useCreateComment(meetingId: number | string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { transcript_segment_id: number; text: string }) =>
      apiFetch(`/meetings/${meetingId}/comments`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['transcript', meetingId] });
    },
  });
}

export function useCreateHighlight(meetingId: number | string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { transcript_segment_id: number; color: string; note: string }) =>
      apiFetch(`/meetings/${meetingId}/highlights`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['highlights', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['transcript', meetingId] });
    },
  });
}
