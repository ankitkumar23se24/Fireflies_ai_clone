import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';

export function useActionItems(meetingId: number | string | undefined) {
  return useQuery({
    queryKey: ['action-items', meetingId],
    queryFn: () => apiFetch<Array<{ id: number; title: string; status: string; assignee?: string | null; due_date?: string | null; description?: string | null }>>(`/meetings/${meetingId}/action-items`),
    enabled: !!meetingId,
  });
}

export function useCreateActionItem(meetingId: number | string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { title: string; assignee?: string; due_date?: string; description?: string }) =>
      apiFetch(`/meetings/${meetingId}/action-items`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['action-items', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['analytics', 'overview'] });
    },
  });
}

export function useUpdateActionItem(meetingId: number | string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, payload }: { itemId: number; payload: { status?: string; assignee?: string; due_date?: string; description?: string } }) =>
      apiFetch(`/action-items/${itemId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['action-items', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meeting', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['analytics', 'overview'] });
    },
  });
}

export function useDeleteActionItem(meetingId: number | string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: number) =>
      apiFetch(`/action-items/${itemId}`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['action-items', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meeting', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['analytics', 'overview'] });
    },
  });
}
