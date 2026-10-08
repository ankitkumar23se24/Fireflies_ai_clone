import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

import DashboardPage from './page';

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client }, children);
  };
}

describe('dashboard', () => {
  it('displays the backend total instead of the recent-meetings page size', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/analytics/overview')) {
        return Promise.resolve(new Response(JSON.stringify({
          total_meetings: 27,
          total_seconds: 3600,
          average_seconds: 1200,
          meetings_this_week: 4,
          meetings_this_month: 12,
          action_items_total: 16,
          action_items_completed: 9,
          completion_rate: 56,
          meetings_per_week: [],
          duration_trend: [],
          action_item_status: [],
        }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ items: [], total: 27, page: 1, page_size: 6 }), { status: 200 }));
    });
    vi.stubGlobal('fetch', fetchMock);

    render(createElement(DashboardPage), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('27')).toBeTruthy();
    });
    expect(screen.getByText('Total meetings')).toBeTruthy();
  });
});
