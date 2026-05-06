export type Conversation = {
  id: string;
  title: string | null;
  project_id: string | null;
  model: string | null;
  created_at: number;
  updated_at: number;
  pinned: 0 | 1;
  archived: 0 | 1;
  context_chat_ids: string; // JSON array
  summary: string | null;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model: string | null;
  created_at: number;
  metadata: string; // JSON object
};

export type Project = {
  id: string;
  name: string;
  color: string;
  icon: string | null;
  created_at: number;
};

export type Memory = {
  id: string;
  type: string;
  content: string;
  embedding: string | null;
  source_chat_id: string | null;
  created_at: number;
  access_count: number;
};

export type AutomationJob = {
  id: string;
  name: string;
  cron_expression: string;
  prompt: string;
  model: string | null;
  enabled: 0 | 1;
  last_run: number | null;
  next_run: number | null;
  created_at: number;
};

export type ConnectedApp = {
  id: string;
  name: string;
  provider: string;
  config: string; // JSON object
  status: string;
  last_sync: number | null;
  created_at: number;
};

export type Notification = {
  id: string;
  type: string;
  title: string;
  body: string;
  read: 0 | 1;
  created_at: number;
};
