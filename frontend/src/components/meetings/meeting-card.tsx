import Link from 'next/link';
import { format } from 'date-fns';
import { ArrowRight, Clock3, Mic, Sparkles } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import type { MeetingListItem } from '@/types/meeting';

export function MeetingCard({ meeting }: { meeting: MeetingListItem }) {
  return (
    <Card className="overflow-hidden transition hover:shadow-lg">
      <CardContent className="p-5">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="secondary">{meeting.status}</Badge>
              <span className="text-xs text-muted-foreground">{meeting.participants.length} participants</span>
            </div>
            <h3 className="text-xl font-semibold">{meeting.title}</h3>
          </div>
          <Link href={`/meetings/${meeting.id}`}>
            <Button variant="ghost" size="sm" className="gap-2">
              Open <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <p className="mb-4 line-clamp-3 text-sm text-muted-foreground">
          {meeting.summary_preview || meeting.description || 'No summary available yet.'}
        </p>

        <div className="mb-4 flex flex-wrap gap-2">
          {meeting.tags.map((tag) => (
            <Badge key={tag.id} variant="outline">
              #{tag.name}
            </Badge>
          ))}
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Mic className="h-3.5 w-3.5" />
            {format(new Date(meeting.date), 'MMM d, yyyy')}
          </div>
          <div className="flex items-center gap-2">
            <Clock3 className="h-3.5 w-3.5" />
            {Math.round(meeting.duration_seconds / 60)} min
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5" />
            {meeting.action_item_count} actions
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
