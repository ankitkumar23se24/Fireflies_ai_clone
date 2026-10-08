'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, CheckCheck, MessageSquareText, Search, Sparkles, Video } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { TranscriptPanel } from '@/components/transcript/transcript-panel';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useActionItems, useCreateActionItem, useDeleteActionItem, useUpdateActionItem } from '@/hooks/use-action-items';
import { useCreateComment, useCreateHighlight } from '@/hooks/use-comments';
import { useMeeting } from '@/hooks/use-meetings';
import { useTranscript } from '@/hooks/use-transcript';
import { useAskMeeting, useGenerateSummary } from '@/hooks/use-ai';

const actionItemSchema = z.object({
  title: z.string().trim().min(1, 'Title is required'),
  assignee: z.string().trim().optional(),
  due_date: z.string().optional(),
  description: z.string().trim().optional(),
});

export default function MeetingDetailPage() {
  const params = useParams<{ meetingId: string }>();
  const meetingId = Number(params.meetingId);
  const validMeetingId = Number.isSafeInteger(meetingId) && meetingId > 0;
  const [transcriptFilter, setTranscriptFilter] = useState('');
  const [question, setQuestion] = useState('');

  const { data: meeting, isLoading, isError, error, refetch } = useMeeting(validMeetingId ? meetingId : undefined);
  const { data: actionItems = [], isError: actionItemsError, error: actionItemsErrorValue } = useActionItems(validMeetingId ? meetingId : undefined);
  const { data: transcriptData, isLoading: transcriptLoading, isError: transcriptError, error: transcriptErrorValue } = useTranscript(validMeetingId ? meetingId : undefined);
  const createActionItem = useCreateActionItem(meetingId);
  const updateActionItem = useUpdateActionItem(meetingId);
  const deleteActionItem = useDeleteActionItem(meetingId);
  const createComment = useCreateComment(meetingId);
  const createHighlight = useCreateHighlight(meetingId);
  const generateSummary = useGenerateSummary(meetingId);
  const askMeeting = useAskMeeting(meetingId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(actionItemSchema),
    defaultValues: { title: '', assignee: '', due_date: '', description: '' },
  });

  const transcriptSegments = (transcriptData?.segments ?? []).filter((segment) => {
    if (!transcriptFilter.trim()) return true;
    const haystack = `${segment.speaker} ${segment.text}`.toLowerCase();
    return haystack.includes(transcriptFilter.toLowerCase());
  });

  const onSubmit = handleSubmit((values) => {
    createActionItem.mutate({
      title: values.title,
      assignee: values.assignee || undefined,
      due_date: values.due_date || undefined,
      description: values.description || undefined,
    }, {
      onSuccess: () => reset(),
    });
  });

  const handleAddComment = (segmentId: number, text: string) => {
    createComment.mutate({ transcript_segment_id: segmentId, text });
  };

  const handleAddHighlight = (segmentId: number, note: string, color: string) => {
    createHighlight.mutate({ transcript_segment_id: segmentId, note, color });
  };

  const handleAsk = () => {
    const trimmedQuestion = question.trim();
    if (trimmedQuestion) askMeeting.mutate(trimmedQuestion);
  };

  if (!validMeetingId) {
    return <div role="alert" className="text-destructive">Invalid meeting ID.</div>;
  }

  if (isLoading) {
    return <div className="text-muted-foreground">Loading meeting…</div>;
  }

  if (isError) {
    return (
      <div role="alert" className="space-y-3 text-destructive">
        <p>Unable to load this meeting: {error instanceof Error ? error.message : 'Please try again.'}</p>
        <Button variant="outline" onClick={() => void refetch()}>Retry</Button>
        <Link href="/meetings" className="ml-3 text-primary">Back to meetings</Link>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div role="alert" className="space-y-3">
        <p>Meeting not found.</p>
        <Link href="/meetings" className="text-primary">Back to meetings</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <Link href="/meetings">
            <Button variant="ghost" size="icon" aria-label="Back to meetings">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Meeting detail</p>
            <h1 className="mt-1 text-3xl font-semibold">{meeting.title}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{meeting.status}</Badge>
          <Button
            variant="outline"
            onClick={() => generateSummary.mutate()}
            disabled={generateSummary.isPending}
          >
            {generateSummary.isPending ? 'Generating…' : 'Generate summary'}
          </Button>
        </div>
      </div>
      {generateSummary.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Summary generation failed: {generateSummary.error instanceof Error ? generateSummary.error.message : 'Please try again.'}
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-4 w-4" />
              Media
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-40 items-center justify-center rounded-xl bg-secondary text-sm text-muted-foreground">
              {meeting.media_url ? 'Media available' : 'Media placeholder'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-7 text-foreground">
              {meeting.summary?.overview || 'No summary generated yet.'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCheck className="h-4 w-4" />
              Action items
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {actionItemsError ? (
              <p role="alert" className="text-sm text-destructive">
                Unable to load action items: {actionItemsErrorValue instanceof Error ? actionItemsErrorValue.message : 'Please try again.'}
              </p>
            ) : null}
            {updateActionItem.isError || deleteActionItem.isError ? (
              <p role="alert" className="text-sm text-destructive">
                Unable to update action items: {
                  (updateActionItem.error || deleteActionItem.error) instanceof Error
                    ? (updateActionItem.error || deleteActionItem.error)?.message
                    : 'Please try again.'
                }
              </p>
            ) : null}
            {actionItems.length ? (
              actionItems.map((item) => (
                <div key={item.id} className="rounded-lg border border-border bg-secondary/30 p-2 text-sm">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="font-medium">{item.title}</div>
                      <div className="text-xs text-muted-foreground">
                        {item.assignee || 'Unassigned'} • {item.status}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          updateActionItem.mutate({
                            itemId: item.id,
                            payload: { status: item.status === 'DONE' ? 'TODO' : 'DONE' },
                          })
                        }
                      >
                        {item.status === 'DONE' ? 'Reopen' : 'Done'}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteActionItem.mutate(item.id)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No action items yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.5fr_0.7fr]">
        <Card>
          <CardContent className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                value={transcriptFilter}
                onChange={(event) => setTranscriptFilter(event.target.value)}
                placeholder="Search transcript by speaker or keyword"
              />
            </div>
            <TranscriptPanel
              segments={transcriptSegments}
              onAddComment={handleAddComment}
              onAddHighlight={handleAddHighlight}
            />
            {transcriptLoading ? <p className="mt-3 text-sm text-muted-foreground">Loading transcript…</p> : null}
            {transcriptError ? (
              <p role="alert" className="mt-3 text-sm text-destructive">
                Unable to load transcript: {transcriptErrorValue instanceof Error ? transcriptErrorValue.message : 'Please try again.'}
              </p>
            ) : null}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Meeting details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div>Participants: {meeting.participants.map((person) => person.name).join(', ') || 'No attendees'}</div>
              <div>Started: {new Date(meeting.date).toLocaleDateString()}</div>
              <div>Duration: {meeting.duration_seconds}s</div>
              <div>Topics: {meeting.topics.length}</div>
              <div>Transcript lines: {transcriptSegments.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquareText className="h-4 w-4" />
                AI Q&A
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about the meeting"
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    handleAsk();
                  }
                }}
              />
              <Button onClick={handleAsk} className="w-full" disabled={!question.trim() || askMeeting.isPending}>
                {askMeeting.isPending ? 'Asking…' : 'Ask'}
              </Button>
              {askMeeting.isError ? (
                <p role="alert" className="text-sm text-destructive">
                  Question failed: {askMeeting.error instanceof Error ? askMeeting.error.message : 'Please try again.'}
                </p>
              ) : null}
              {askMeeting.data ? (
                <div className="space-y-2 rounded-xl bg-secondary/30 p-3 text-sm text-foreground">
                  <p>{askMeeting.data.answer}</p>
                  {askMeeting.data.citations.map((citation) => (
                    <blockquote key={citation.segment_id} className="border-l-2 border-primary/50 pl-3 text-xs text-muted-foreground">
                      {citation.speaker} · {Math.floor(citation.timestamp / 60)}:{String(Math.floor(citation.timestamp % 60)).padStart(2, '0')} — {citation.text}
                    </blockquote>
                  ))}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Add action item</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-3">
                {createActionItem.isError ? (
                  <p role="alert" className="text-sm text-destructive">
                    Unable to create action item: {createActionItem.error instanceof Error ? createActionItem.error.message : 'Please try again.'}
                  </p>
                ) : null}
                <div>
                  <Input {...register('title')} placeholder="Action item title" />
                  {errors.title && <p className="mt-1 text-xs text-red-500">{String(errors.title.message)}</p>}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input {...register('assignee')} placeholder="Assignee" />
                  <Input {...register('due_date')} type="date" />
                </div>
                <Input {...register('description')} placeholder="Details" />
                <Button type="submit" className="w-full" disabled={createActionItem.isPending}>
                  {createActionItem.isPending ? 'Saving…' : 'Create action item'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
