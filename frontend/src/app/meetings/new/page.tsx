'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { apiFetch } from '@/lib/api';

export default function NewMeetingPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [transcript, setTranscript] = useState('[00:02] Ankit: Let\'s go through the next milestone.\n[00:10] Rahul: We will launch the API next week.');
  const [participants, setParticipants] = useState('Ankit, Rahul');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);

    try {
      const payload = {
        title: title || 'Imported meeting',
        participants: participants
          .split(',')
          .map((name) => name.trim())
          .filter(Boolean)
          .map((name) => ({ name })),
        transcript_text: transcript,
      };

      const meeting = await apiFetch<{ id: number }>('/meetings', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      router.push(`/meetings/${meeting.id}`);
    } catch {
      alert('Unable to create meeting right now.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">Capture</p>
        <h1 className="mt-2 text-3xl font-semibold">Create meeting</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Import transcript or start from a blank brief</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium">Meeting title</label>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Quarterly planning session" />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">Participants</label>
              <Input value={participants} onChange={(event) => setParticipants(event.target.value)} placeholder="Ankit, Rahul, Priya" />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">Transcript</label>
              <textarea
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                rows={14}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create meeting'}</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
