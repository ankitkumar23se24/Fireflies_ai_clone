'use client';

import Link from 'next/link';
import { Activity, CheckCheck, CircleDot, Mic, Users } from 'lucide-react';

import { MeetingCard } from '@/components/meetings/meeting-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAnalyticsOverview } from '@/hooks/use-analytics';
import { useMeetings } from '@/hooks/use-meetings';

export default function DashboardPage() {
  const { data: meetingPage, isLoading, isError, error, refetch } = useMeetings('', 1, 6);
  const { data: analytics, isError: analyticsError } = useAnalyticsOverview();
  const meetings = meetingPage?.items ?? [];

  const stats = [
    { label: 'Total meetings', value: String(analytics?.total_meetings ?? meetingPage?.total ?? 0), icon: Mic },
    { label: 'Action items', value: String(analytics?.action_items_total ?? 0), icon: CheckCheck },
    { label: 'Avg. duration', value: `${Math.round((analytics?.average_seconds ?? 0) / 60)}m`, icon: Activity },
    { label: 'Recent attendees', value: String(meetings.reduce((sum, item) => sum + item.participants.length, 0)), icon: Users },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">Overview</p>
          <h1 className="mt-2 text-3xl font-semibold">Your meeting workspace</h1>
        </div>
        <Link href="/meetings/new">
          <Button>Create meeting</Button>
        </Link>
      </div>

      {analyticsError ? (
        <p role="alert" className="text-sm text-destructive">
          Workspace analytics are unavailable. Meeting list totals are shown where possible.
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-2 text-2xl font-semibold">{value}</p>
              </div>
              <div className="rounded-xl bg-secondary p-2">
                <Icon className="h-5 w-5 text-primary" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>High signal updates</CardTitle>
          </div>
          <Badge variant="secondary" className="gap-2">
            <CircleDot className="h-3 w-3 fill-current" />
            Live sync
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-dashed border-border p-4">
              <div className="text-sm text-muted-foreground">Top insight</div>
              <div className="mt-2 text-lg font-medium">Pipeline signal is improving across customer calls.</div>
            </div>
            <div className="rounded-xl border border-dashed border-border p-4">
              <div className="text-sm text-muted-foreground">Next review</div>
              <div className="mt-2 text-lg font-medium">Customer success sync is scheduled this afternoon.</div>
            </div>
            <div className="rounded-xl border border-dashed border-border p-4">
              <div className="text-sm text-muted-foreground">Automations</div>
              <div className="mt-2 text-lg font-medium">Three follow-up workflows are ready to publish.</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-semibold">Recent meetings</h2>
          <Link href="/meetings" className="text-sm font-medium text-primary">
            View all
          </Link>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {isLoading ? <div className="text-muted-foreground">Loading meetings…</div> : null}
          {isError ? (
            <div role="alert" className="text-sm text-destructive">
              Unable to load recent meetings: {error instanceof Error ? error.message : 'Please try again.'}
              <Button className="ml-2" variant="outline" size="sm" onClick={() => void refetch()}>Retry</Button>
            </div>
          ) : null}
          {!isLoading && !isError && meetings.length === 0 ? (
            <p className="text-muted-foreground">No meetings yet. Create or import a meeting to get started.</p>
          ) : null}
          {!isError && meetings.map((meeting) => <MeetingCard key={meeting.id} meeting={meeting} />)}
        </div>
      </div>
    </div>
  );
}
