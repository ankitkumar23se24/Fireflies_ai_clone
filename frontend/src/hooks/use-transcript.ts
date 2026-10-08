import { useQuery } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';
import type { TranscriptSegment } from '@/types/meeting';

export function useTranscript(meetingId: number | string | undefined) {
  return useQuery({
    queryKey: ['transcript', meetingId],
    queryFn: () => apiFetch<{ segments: TranscriptSegment[]; speakers: string[] }>(`/meetings/${meetingId}/transcript`),
    enabled: !!meetingId,
  });
}
