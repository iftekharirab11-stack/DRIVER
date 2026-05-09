import db from './database';
import { v4 as uuidv4 } from 'uuid';
import type {
  Conversation,
  Message,
  Project,
  Memory,
  AutomationJob,
  ConnectedApp,
  Notification,
} from '../../types';

const createId = (): string => uuidv4();

// ── Conversations ─────────────────────────────────────────────────────────────

export function getAllConversations(): Conversation[] {
  return db.prepare('SELECT * FROM conversations ORDER BY updated_at DESC').all() as Conversation[];
}

export function getConversationById(id: string): Conversation | undefined {
  return db.prepare('SELECT * FROM conversations WHERE id = ?').get(id) as Conversation | undefined;
}

export function getConversationsByProject(projectId: string | null): Conversation[] {
  if (projectId === null) {
    return db.prepare('SELECT * FROM conversations WHERE project_id IS NULL ORDER BY updated_at DESC').all() as Conversation[];
  }
  return db.prepare('SELECT * FROM conversations WHERE project_id = ? ORDER BY updated_at DESC').all(projectId) as Conversation[];
}

export function createConversation(data: {
  title?: string;
  project_id?: string | null;
  model?: string;
  context_chat_ids?: string[];
  summary?: string;
}): Conversation {
  const now = Date.now();
  const id = createId();
  db.prepare(`
    INSERT INTO conversations (id, title, project_id, model, created_at, updated_at, context_chat_ids, summary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    data.title || null,
    data.project_id || null,
    data.model || 'claude-sonnet-4-5',
    now,
    now,
    JSON.stringify(data.context_chat_ids || []),
    data.summary || null
  );
  return getConversationById(id)!;
}

export function updateConversation(id: string, data: Partial<Pick<Conversation, 'title' | 'project_id' | 'model' | 'pinned' | 'archived' | 'context_chat_ids' | 'summary'>>): Conversation | undefined {
  const existing = getConversationById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.title !== undefined) {
    updates.push('title = ?');
    values.push(data.title);
  }
  if (data.project_id !== undefined) {
    updates.push('project_id = ?');
    values.push(data.project_id);
  }
  if (data.model !== undefined) {
    updates.push('model = ?');
    values.push(data.model);
  }
  if (data.pinned !== undefined) {
    updates.push('pinned = ?');
    values.push(data.pinned ? 1 : 0);
  }
  if (data.archived !== undefined) {
    updates.push('archived = ?');
    values.push(data.archived ? 1 : 0);
  }
  if (data.context_chat_ids !== undefined) {
    updates.push('context_chat_ids = ?');
    values.push(JSON.stringify(data.context_chat_ids));
  }
  if (data.summary !== undefined) {
    updates.push('summary = ?');
    values.push(data.summary);
  }

  if (updates.length > 0) {
    updates.push('updated_at = ?');
    values.push(Date.now());
    values.push(id);
    db.prepare(`UPDATE conversations SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getConversationById(id);
}

export function deleteConversation(id: string): boolean {
  const result = db.prepare('DELETE FROM conversations WHERE id = ?').run(id);
  return result.changes > 0;
}

export function searchConversations(query: string): Conversation[] {
  const pattern = `%${query}%`;
  return db.prepare('SELECT * FROM conversations WHERE title LIKE ? ORDER BY updated_at DESC').all(pattern) as Conversation[];
}

// ── Messages ───────────────────────────────────────────────────────────────────

export function getAllMessages(): Message[] {
  return db.prepare('SELECT * FROM messages ORDER BY created_at DESC').all() as Message[];
}

export function getMessagesByConversation(conversationId: string): Message[] {
  return db.prepare('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC').all(conversationId) as Message[];
}

export function getMessageById(id: string): Message | undefined {
  return db.prepare('SELECT * FROM messages WHERE id = ?').get(id) as Message | undefined;
}

export function createMessage(data: {
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model?: string;
  metadata?: Record<string, any>;
}): Message {
  const id = createId();
  db.prepare(`
    INSERT INTO messages (id, conversation_id, role, content, model, created_at, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    data.conversation_id,
    data.role,
    data.content,
    data.model || null,
    Date.now(),
    JSON.stringify(data.metadata || {})
  );
  return getMessageById(id)!;
}

export function updateMessage(id: string, data: Partial<Pick<Message, 'content' | 'metadata'>>): Message | undefined {
  const existing = getMessageById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.content !== undefined) {
    updates.push('content = ?');
    values.push(data.content);
  }
  if (data.metadata !== undefined) {
    updates.push('metadata = ?');
    values.push(JSON.stringify(data.metadata));
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE messages SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getMessageById(id);
}

export function deleteMessage(id: string): boolean {
  const result = db.prepare('DELETE FROM messages WHERE id = ?').run(id);
  return result.changes > 0;
}

export function deleteMessagesByConversation(conversationId: string): void {
  db.prepare('DELETE FROM messages WHERE conversation_id = ?').run(conversationId);
}

// ── Projects ───────────────────────────────────────────────────────────────────

export function getAllProjects(): Project[] {
  return db.prepare('SELECT * FROM projects ORDER BY created_at DESC').all() as Project[];
}

export function getProjectById(id: string): Project | undefined {
  return db.prepare('SELECT * FROM projects WHERE id = ?').get(id) as Project | undefined;
}

export function createProject(data: { name: string; color?: string; icon?: string }): Project {
  const id = createId();
  db.prepare(`
    INSERT INTO projects (id, name, color, icon, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(id, data.name, data.color || '#534AB7', data.icon || null, Date.now());
  return getProjectById(id)!;
}

export function updateProject(id: string, data: Partial<Pick<Project, 'name' | 'color' | 'icon'>>): Project | undefined {
  const existing = getProjectById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.name !== undefined) {
    updates.push('name = ?');
    values.push(data.name);
  }
  if (data.color !== undefined) {
    updates.push('color = ?');
    values.push(data.color);
  }
  if (data.icon !== undefined) {
    updates.push('icon = ?');
    values.push(data.icon);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE projects SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getProjectById(id);
}

export function deleteProject(id: string): boolean {
  // Set conversation project_id to NULL before deleting
  db.prepare('UPDATE conversations SET project_id = NULL WHERE project_id = ?').run(id);
  const result = db.prepare('DELETE FROM projects WHERE id = ?').run(id);
  return result.changes > 0;
}

// ── Memory ─────────────────────────────────────────────────────────────────────

export function getAllMemory(): Memory[] {
  return db.prepare('SELECT * FROM memory ORDER BY access_count DESC, created_at DESC').all() as Memory[];
}

export function getMemoryById(id: string): Memory | undefined {
  return db.prepare('SELECT * FROM memory WHERE id = ?').get(id) as Memory | undefined;
}

export function getMemoryByType(type: string): Memory[] {
  return db.prepare('SELECT * FROM memory WHERE type = ? ORDER BY access_count DESC, created_at DESC').all(type) as Memory[];
}

export function searchMemory(query: string): Memory[] {
  const pattern = `%${query}%`;
  return db.prepare('SELECT * FROM memory WHERE content LIKE ? ORDER BY access_count DESC LIMIT 50').all(pattern) as Memory[];
}

export function createMemory(data: {
  type: string;
  content: string;
  embedding?: string | null;
  source_chat_id?: string | null;
}): Memory {
  const id = createId();
  db.prepare(`
    INSERT INTO memory (id, type, content, embedding, source_chat_id, created_at, access_count)
    VALUES (?, ?, ?, ?, ?, ?, 0)
  `).run(id, data.type, data.content, data.embedding || null, data.source_chat_id || null, Date.now());
  return getMemoryById(id)!;
}

export function updateMemory(id: string, data: Partial<Pick<Memory, 'content' | 'embedding'>>): Memory | undefined {
  const existing = getMemoryById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.content !== undefined) {
    updates.push('content = ?');
    values.push(data.content);
  }
  if (data.embedding !== undefined) {
    updates.push('embedding = ?');
    values.push(data.embedding);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE memory SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getMemoryById(id);
}

export function incrementMemoryAccess(id: string): void {
  db.prepare('UPDATE memory SET access_count = access_count + 1 WHERE id = ?').run(id);
}

export function deleteMemory(id: string): boolean {
  const result = db.prepare('DELETE FROM memory WHERE id = ?').run(id);
  return result.changes > 0;
}

// ── Automation Jobs ────────────────────────────────────────────────────────────

export function getAllAutomationJobs(): AutomationJob[] {
  return db.prepare('SELECT * FROM automation_jobs ORDER BY next_run ASC').all() as AutomationJob[];
}

export function getAutomationJobById(id: string): AutomationJob | undefined {
  return db.prepare('SELECT * FROM automation_jobs WHERE id = ?').get(id) as AutomationJob | undefined;
}

export function getEnabledAutomationJobs(): AutomationJob[] {
  return db.prepare('SELECT * FROM automation_jobs WHERE enabled = 1 ORDER BY next_run ASC').all() as AutomationJob[];
}

export function createAutomationJob(data: {
  name: string;
  cron_expression: string;
  prompt: string;
  model?: string;
  enabled?: boolean;
  next_run?: number | null;
}): AutomationJob {
  const id = createId();
  db.prepare(`
    INSERT INTO automation_jobs (id, name, cron_expression, prompt, model, enabled, last_run, next_run, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    data.name,
    data.cron_expression,
    data.prompt,
    data.model || null,
    data.enabled ? 1 : 0,
    null,
    data.next_run || null,
    Date.now()
  );
  return getAutomationJobById(id)!;
}

export function updateAutomationJob(id: string, data: Partial<Pick<AutomationJob, 'name' | 'cron_expression' | 'prompt' | 'model' | 'enabled' | 'last_run' | 'next_run'>>): AutomationJob | undefined {
  const existing = getAutomationJobById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.name !== undefined) {
    updates.push('name = ?');
    values.push(data.name);
  }
  if (data.cron_expression !== undefined) {
    updates.push('cron_expression = ?');
    values.push(data.cron_expression);
  }
  if (data.prompt !== undefined) {
    updates.push('prompt = ?');
    values.push(data.prompt);
  }
  if (data.model !== undefined) {
    updates.push('model = ?');
    values.push(data.model);
  }
  if (data.enabled !== undefined) {
    updates.push('enabled = ?');
    values.push(data.enabled ? 1 : 0);
  }
  if (data.last_run !== undefined) {
    updates.push('last_run = ?');
    values.push(data.last_run);
  }
  if (data.next_run !== undefined) {
    updates.push('next_run = ?');
    values.push(data.next_run);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE automation_jobs SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getAutomationJobById(id);
}

export function deleteAutomationJob(id: string): boolean {
  const result = db.prepare('DELETE FROM automation_jobs WHERE id = ?').run(id);
  return result.changes > 0;
}

// ── Connected Apps ─────────────────────────────────────────────────────────────

export function getAllConnectedApps(): ConnectedApp[] {
  return db.prepare('SELECT * FROM connected_apps ORDER BY last_sync DESC').all() as ConnectedApp[];
}

export function getConnectedAppById(id: string): ConnectedApp | undefined {
  return db.prepare('SELECT * FROM connected_apps WHERE id = ?').get(id) as ConnectedApp | undefined;
}

export function getConnectedAppsByProvider(provider: string): ConnectedApp[] {
  return db.prepare('SELECT * FROM connected_apps WHERE provider = ? ORDER BY last_sync DESC').all(provider) as ConnectedApp[];
}

export function createConnectedApp(data: {
  name: string;
  provider: string;
  config?: Record<string, any>;
  status?: string;
}): ConnectedApp {
  const id = createId();
  db.prepare(`
    INSERT INTO connected_apps (id, name, provider, config, status, created_at, last_sync)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    data.name,
    data.provider,
    JSON.stringify(data.config || {}),
    data.status || 'connected',
    Date.now(),
    Date.now()
  );
  return getConnectedAppById(id)!;
}

export function updateConnectedApp(id: string, data: Partial<Pick<ConnectedApp, 'name' | 'config' | 'status' | 'last_sync'>>): ConnectedApp | undefined {
  const existing = getConnectedAppById(id);
  if (!existing) return undefined;

  const updates: string[] = [];
  const values: any[] = [];

  if (data.name !== undefined) {
    updates.push('name = ?');
    values.push(data.name);
  }
  if (data.config !== undefined) {
    updates.push('config = ?');
    values.push(JSON.stringify(data.config));
  }
  if (data.status !== undefined) {
    updates.push('status = ?');
    values.push(data.status);
  }
  if (data.last_sync !== undefined) {
    updates.push('last_sync = ?');
    values.push(data.last_sync);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE connected_apps SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getConnectedAppById(id);
}

export function deleteConnectedApp(id: string): boolean {
  const result = db.prepare('DELETE FROM connected_apps WHERE id = ?').run(id);
  return result.changes > 0;
}

// ── Notifications ──────────────────────────────────────────────────────────────

export function getAllNotifications(): Notification[] {
  return db.prepare('SELECT * FROM notifications_log ORDER BY created_at DESC').all() as Notification[];
}

export function getUnreadNotifications(): Notification[] {
  return db.prepare('SELECT * FROM notifications_log WHERE read = 0 ORDER BY created_at DESC').all() as Notification[];
}

export function getNotificationById(id: string): Notification | undefined {
  return db.prepare('SELECT * FROM notifications_log WHERE id = ?').get(id) as Notification | undefined;
}

export function createNotification(data: {
  type: string;
  title: string;
  body: string;
  read?: boolean;
}): Notification {
  const id = createId();
  db.prepare(`
    INSERT INTO notifications_log (id, type, title, body, read, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(id, data.type, data.title, data.body, data.read ? 1 : 0, Date.now());
  return getNotificationById(id)!;
}

export function markNotificationRead(id: string, read = true): Notification | undefined {
  db.prepare('UPDATE notifications_log SET read = ? WHERE id = ?').run(read ? 1 : 0, id);
  return getNotificationById(id);
}

export function markAllNotificationsRead(): void {
  db.prepare('UPDATE notifications_log SET read = 1').run();
}

export function deleteNotification(id: string): boolean {
  const result = db.prepare('DELETE FROM notifications_log WHERE id = ?').run(id);
  return result.changes > 0;
}
