'use client';

import Link from 'next/link';
import { Filter, Plus, Search } from 'lucide-react';
import { useState } from 'react';

import { MeetingCard } from '@/components/meetings/meeting-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useMeetings } from '@/hooks/use-meetings';

export default function MeetingsPage() {
  const [query, setQuery] = useState('');
  const { data: meetingPage, isLoading, isError, error, refetch } = useMeetings(query, 1, 12);
  const meetings = meetingPage?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">Library</p>
          <h1 className="mt-2 text-3xl font-semibold">All meetings</h1>
        </div>
        <Link href="/meetings/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" /> New meeting
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pl-9"
              placeholder="Filter by title, participant, transcript…"
            />
          </div>
          <Button variant="secondary" className="gap-2">
            <Filter className="h-4 w-4" /> More filters
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {isLoading ? <p className="text-muted-foreground">Loading meetings…</p> : null}
        {isError ? (
          <p role="alert" className="text-sm text-destructive">
            Unable to load meetings: {error instanceof Error ? error.message : 'Please try again.'}{' '}
            <Button variant="outline" size="sm" onClick={() => void refetch()}>Retry</Button>
          </p>
        ) : null}
        {!isLoading && !isError && meetings.length === 0 ? <p className="text-muted-foreground">No meetings found.</p> : null}
        {!isError && meetings.map((meeting) => <MeetingCard key={meeting.id} meeting={meeting} />)}
      </div>
    </div>
  );
}
