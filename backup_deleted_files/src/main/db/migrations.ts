import Database from 'better-sqlite3';

/**
 * Run all schema migrations. Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
 */
export function runMigrations(db: Database.Database): void {
  db.exec(`
    -- conversations
    CREATE TABLE IF NOT EXISTS conversations (
      id TEXT PRIMARY KEY,
      title TEXT,
      project_id TEXT,
      model TEXT DEFAULT 'claude-sonnet-4-5',
      created_at INTEGER,
      updated_at INTEGER,
      pinned INTEGER DEFAULT 0,
      archived INTEGER DEFAULT 0,
      context_chat_ids TEXT DEFAULT '[]',
      summary TEXT
    );

    -- messages
    CREATE TABLE IF NOT EXISTS messages (
      id TEXT PRIMARY KEY,
      conversation_id TEXT NOT NULL,
      role TEXT,
      content TEXT,
      model TEXT,
      created_at INTEGER,
      metadata TEXT DEFAULT '{}',
      FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );

    -- projects
    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY,
      name TEXT,
      color TEXT DEFAULT '#534AB7',
      icon TEXT,
      created_at INTEGER
    );

    -- memory (vector / semantic memory store)
    CREATE TABLE IF NOT EXISTS memory (
      id TEXT PRIMARY KEY,
      type TEXT,
      content TEXT,
      embedding TEXT,
      source_chat_id TEXT,
      created_at INTEGER,
      access_count INTEGER DEFAULT 0
    );

    -- automation_jobs (scheduled tasks)
    CREATE TABLE IF NOT EXISTS automation_jobs (
      id TEXT PRIMARY KEY,
      name TEXT,
      cron_expression TEXT,
      prompt TEXT,
      model TEXT,
      enabled INTEGER DEFAULT 1,
      last_run INTEGER,
      next_run INTEGER,
      created_at INTEGER
    );

    -- connected_apps (OAuth connections like Google, GitHub, etc.)
    CREATE TABLE IF NOT EXISTS connected_apps (
      id TEXT PRIMARY KEY,
      name TEXT,
      provider TEXT,
      config TEXT DEFAULT '{}',
      status TEXT DEFAULT 'connected',
      last_sync INTEGER,
      created_at INTEGER
    );

    -- notifications_log
    CREATE TABLE IF NOT EXISTS notifications_log (
      id TEXT PRIMARY KEY,
      type TEXT,
      title TEXT,
      body TEXT,
      read INTEGER DEFAULT 0,
      created_at INTEGER
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);
    CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
  `);
}
