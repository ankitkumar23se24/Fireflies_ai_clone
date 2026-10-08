export type MeetingStatus = 'COMPLETED' | 'PROCESSING' | 'FAILED';

export interface Participant {
  id: number;
  name: string;
  email?: string | null;
  role?: string | null;
}

export interface Tag {
  id: number;
  name: string;
}

export interface TranscriptSegment {
  id: number;
  speaker: string;
  start_time: number;
  end_time: number;
  text: string;
  sequence_number: number;
  comments: Array<{ id: number; text: string; created_at: string }>;
  highlights: Array<{ id: number; color: string; note: string }>;
}

export interface Summary {
  overview: string;
  key_takeaways: string[];
  decisions: string[];
  follow_ups: string[];
  generated_by: string;
  generated_at: string;
}

export interface Meeting {
  id: number;
  title: string;
  description?: string | null;
  date: string;
  duration_seconds: number;
  media_url?: string | null;
  status: MeetingStatus;
  participants: Participant[];
  tags: Tag[];
  summary?: Summary | null;
  topics: Array<{ id: number; name: string; start_time: number; end_time: number }>;
  chapters: Array<{ id: number; title: string; summary: string; start_time: number; end_time: number }>;
  action_items: Array<{ id: number; title: string; status: string; assignee?: string | null; due_date?: string | null; description?: string | null }>;
}

export interface MeetingListItem extends Omit<Meeting, 'summary' | 'topics' | 'chapters' | 'action_items'> {
  summary_preview?: string | null;
  action_item_count: number;
}

export interface MeetingPageResponse {
  items: MeetingListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchHit {
  type: string;
  meeting_id: number;
  meeting_title: string;
  meeting_date: string;
  text: string;
  timestamp?: number | null;
  segment_id?: number | null;
  participant?: string | null;
}

export interface SearchResults {
  query: string;
  total: number;
  hits: SearchHit[];
}
