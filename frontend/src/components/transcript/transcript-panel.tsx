'use client';

import { Clock3, MessageSquareText, Search } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { TranscriptSegment } from '@/types/meeting';

export function TranscriptPanel({
  segments,
  onAddComment,
  onAddHighlight,
}: {
  segments: TranscriptSegment[];
  onAddComment?: (segmentId: number, text: string) => void;
  onAddHighlight?: (segmentId: number, note: string, color: string) => void;
}) {
  const [commentDrafts, setCommentDrafts] = useState<Record<number, string>>({});
  const [highlightDrafts, setHighlightDrafts] = useState<Record<number, { note: string; color: string }>>({});

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Transcript</h3>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Search className="h-4 w-4" />
          {segments.length} lines in view
        </div>
      </div>

      <div className="space-y-3">
        {segments.map((segment) => (
          <div key={segment.id} className="rounded-xl border border-border bg-secondary/30 p-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{segment.speaker}</Badge>
                <span className="text-xs text-muted-foreground">#{segment.sequence_number}</span>
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock3 className="h-3.5 w-3.5" />
                {segment.start_time.toFixed(1)}s
              </div>
            </div>
            <p className="text-sm leading-7 text-foreground">{segment.text}</p>

            {segment.highlights?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {segment.highlights.map((highlight) => (
                  <Badge key={highlight.id} variant="outline" className="border-amber-400/60 bg-amber-100 text-amber-900 dark:bg-amber-500/20 dark:text-amber-100">
                    {highlight.note}
                  </Badge>
                ))}
              </div>
            ) : null}

            {segment.comments?.length ? (
              <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                {segment.comments.map((comment) => (
                  <div key={comment.id} className="flex items-center gap-2">
                    <MessageSquareText className="h-3.5 w-3.5" />
                    {comment.text}
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mt-4 grid gap-2 md:grid-cols-[1fr_auto]">
              <Input
                value={commentDrafts[segment.id] ?? ''}
                onChange={(event) => setCommentDrafts((prev) => ({ ...prev, [segment.id]: event.target.value }))}
                placeholder="Add a comment"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  const text = (commentDrafts[segment.id] || '').trim();
                  if (text && onAddComment) {
                    onAddComment(segment.id, text);
                    setCommentDrafts((prev) => ({ ...prev, [segment.id]: '' }));
                  }
                }}
              >
                Comment
              </Button>
            </div>

            <div className="mt-2 flex items-center gap-2">
              <Input
                value={highlightDrafts[segment.id]?.note ?? ''}
                onChange={(event) =>
                  setHighlightDrafts((prev) => ({
                    ...prev,
                    [segment.id]: { note: event.target.value, color: prev[segment.id]?.color ?? 'yellow' },
                  }))
                }
                placeholder="Highlight note"
              />
              <select
                value={highlightDrafts[segment.id]?.color ?? 'yellow'}
                onChange={(event) =>
                  setHighlightDrafts((prev) => ({
                    ...prev,
                    [segment.id]: { note: prev[segment.id]?.note ?? '', color: event.target.value },
                  }))
                }
                className="h-10 rounded-md border border-input bg-background px-2 text-sm"
              >
                <option value="yellow">Yellow</option>
                <option value="green">Green</option>
                <option value="blue">Blue</option>
                <option value="purple">Purple</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const note = (highlightDrafts[segment.id]?.note || '').trim();
                  if (note && onAddHighlight) {
                    onAddHighlight(segment.id, note, highlightDrafts[segment.id].color);
                    setHighlightDrafts((prev) => ({ ...prev, [segment.id]: { note: '', color: prev[segment.id]?.color ?? 'yellow' } }));
                  }
                }}
              >
                Highlight
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
