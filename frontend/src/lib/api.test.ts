import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiFetch } from './api';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('apiFetch', () => {
  it('returns cleanly for successful no-content responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));

    await expect(apiFetch('/action-items/3', { method: 'DELETE' })).resolves.toBeUndefined();
  });

  it('extracts readable messages from API error envelopes', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ error: { message: 'Meeting not found' } }),
      { status: 404 },
    )));

    await expect(apiFetch('/meetings/999')).rejects.toThrow('Meeting not found');
  });
});
