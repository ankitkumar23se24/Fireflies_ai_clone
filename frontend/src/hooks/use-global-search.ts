import { useQuery } from '@tanstack/react-query';

import { apiFetch } from '@/lib/api';
import type { SearchResults } from '@/types/meeting';

export function useGlobalSearch(query: string) {
  return useQuery({
    queryKey: ['global-search', query],
    queryFn: () => apiFetch<SearchResults>(`/search?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 0,
  });
}
