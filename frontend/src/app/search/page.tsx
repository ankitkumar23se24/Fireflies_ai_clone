'use client';

import { Search } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useGlobalSearch } from '@/hooks/use-global-search';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const { data: results, isLoading } = useGlobalSearch(searchTerm);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">Discovery</p>
        <h1 className="mt-2 text-3xl font-semibold">Global meeting search</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search across meetings and transcripts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input value={query} onChange={(event) => setQuery(event.target.value)} className="pl-9" placeholder="Ask what happened in a call…" />
            </div>
            <Button onClick={() => setSearchTerm(query)} disabled={isLoading || !query.trim()}>{isLoading ? 'Searching…' : 'Search'}</Button>
          </div>

          <div className="rounded-xl border border-border bg-secondary/30 p-4 text-sm text-muted-foreground">
            {results && results.total > 0 ? `${results.total} matches found for “${results.query}”` : 'Search all content across transcript text, summaries, and action items.'}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {results?.hits.map((hit) => (
          <Card key={`${hit.meeting_id}-${hit.segment_id ?? hit.text}`}>
            <CardContent className="p-4">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="font-medium">{hit.meeting_title}</div>
                <div className="text-xs text-muted-foreground">{hit.type}</div>
              </div>
              <p className="text-sm text-foreground">{hit.text}</p>
              <div className="mt-3 text-xs text-muted-foreground">
                {hit.participant ? `${hit.participant} • ` : ''}
                {hit.timestamp !== null ? `@ ${hit.timestamp}s` : 'Meeting match'}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
