import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useAskMeeting, useGenerateSummary } from './use-ai';
import { useUpdateActionItem } from './use-action-items';

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('meeting detail mutations', () => {
  it('generates a summary and updates the cached meeting', async () => {
    const meeting = { id: 7, title: 'Planning', summary: { overview: 'Generated summary' } };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(meeting), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const client = createQueryClient();
    const { result } = renderHook(() => useGenerateSummary(7), { wrapper: createWrapper(client) });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/meetings/7/generate-summary'),
      expect.objectContaining({ method: 'POST' }),
    );
    expect(client.getQueryData(['meeting', 7])).toEqual(meeting);
  });

  it('sends the question and returns the real response with citations', async () => {
    const answer = { answer: 'The team chose SQLite.', citations: [{ segment_id: 2, timestamp: 20, speaker: 'Ankit', text: 'We decided to go with SQLite.' }], provider: 'heuristic' };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(answer), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => useAskMeeting(4), { wrapper: createWrapper(createQueryClient()) });

    await act(async () => {
      await result.current.mutateAsync('Which database did we choose?');
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/meetings/4/ask'),
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ question: 'Which database did we choose?' }) }),
    );
    expect(result.current.data).toEqual(answer);
  });

  it('invalidates the action-item list for its meeting after an update', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const client = createQueryClient();
    client.setQueryData(['action-items', 9], [{ id: 31, title: 'Update docs' }]);
    client.setQueryData(['action-items', 31], [{ id: 31, title: 'Wrong cache key' }]);
    const { result } = renderHook(() => useUpdateActionItem(9), { wrapper: createWrapper(client) });

    await act(async () => {
      await result.current.mutateAsync({ itemId: 31, payload: { status: 'DONE' } });
    });

    await waitFor(() => {
      expect(client.getQueryState(['action-items', 9])?.isInvalidated).toBe(true);
    });
    expect(client.getQueryState(['action-items', 31])?.isInvalidated).toBe(false);
  });
});
