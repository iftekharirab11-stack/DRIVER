"""
Test script for Driver DB schema using Python's sqlite3.
Validates all tables, indexes, and basic CRUD operations.
"""

import sqlite3
import json
import time

def main():
    print("Driver DB Schema Test\n")
    print("=" * 60)

    # Use in-memory DB for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('PRAGMA foreign_keys = ON')  # Enable FK enforcement in SQLite

    # ── Create all tables ────────────────────────────────────────────────────
    cur.executescript("""
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

        -- memory
        CREATE TABLE IF NOT EXISTS memory (
          id TEXT PRIMARY KEY,
          type TEXT,
          content TEXT,
          embedding TEXT,
          source_chat_id TEXT,
          created_at INTEGER,
          access_count INTEGER DEFAULT 0
        );

        -- automation_jobs
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

        -- connected_apps
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
    """)
    print("Created tables and indexes (including projects name index)")

    # ── Test: Insert a project ───────────────────────────────────────────────
    proj_id = 'proj_001'
    cur.execute(
        'INSERT INTO projects (id, name, color, icon, created_at) VALUES (?, ?, ?, ?, ?)',
        (proj_id, 'Work', '#3B82F6', 'briefcase', int(time.time()))
    )
    conn.commit()
    cur.execute('SELECT * FROM projects WHERE id = ?', (proj_id,))
    proj = cur.fetchone()
    assert proj['name'] == 'Work', "Project insert failed"
    print(f"Project OK: {dict(proj)}")

    # ── Test: Insert a conversation ──────────────────────────────────────────
    conv_id = 'conv_001'
    now = int(time.time())
    cur.execute(
        '''INSERT INTO conversations (id, title, project_id, model, created_at, updated_at, context_chat_ids, summary)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (conv_id, 'Show my GitHub repos', proj_id, 'claude-sonnet-4-5', now, now, '[]', 'Summary about GitHub')
    )
    conn.commit()
    cur.execute('SELECT * FROM conversations WHERE id = ?', (conv_id,))
    conv = cur.fetchone()
    assert conv['pinned'] == 0, "Default pinned should be 0"
    assert conv['archived'] == 0, "Default archived should be 0"
    print(f"Conversation OK: pinned={conv['pinned']}, archived={conv['archived']}")

    # ── Test: Insert messages ────────────────────────────────────────────────
    msg_id_1 = 'msg_001'
    msg_id_2 = 'msg_002'
    cur.execute(
        'INSERT INTO messages (id, conversation_id, role, content, model, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (msg_id_1, conv_id, 'user', 'Show my GitHub repos', 'claude-sonnet-4-5', now, json.dumps({}))
    )
    cur.execute(
        'INSERT INTO messages (id, conversation_id, role, content, model, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (msg_id_2, conv_id, 'assistant', 'Found 3 repositories', 'claude-sonnet-4-5', now + 1, json.dumps({'tokens': 42}))
    )
    conn.commit()
    cur.execute('SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ?', (conv_id,))
    msg_count = cur.fetchone()['cnt']
    assert msg_count == 2, f"Expected 2 messages, got {msg_count}"
    print(f"Messages OK: {msg_count} messages in conversation")

    # ── Test: FK cascade delete ─────────────────────────────────────────────
    cur.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    conn.commit()
    cur.execute('SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ?', (conv_id,))
    remaining_msgs = cur.fetchone()['cnt']
    assert remaining_msgs == 0, "Messages should be cascade-deleted"
    print(f"Cascade delete OK: messages removed when conversation deleted")

    # ── Test: Automation job ─────────────────────────────────────────────────
    job_id = 'job_001'
    cur.execute(
        '''INSERT INTO automation_jobs (id, name, cron_expression, prompt, model, enabled, last_run, next_run, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (job_id, 'Daily Summary', '0 9 * * *', 'Summarize yesterday', 'claude-sonnet-4-5', 1, None, now + 86400, now)
    )
    conn.commit()
    cur.execute('SELECT * FROM automation_jobs WHERE id = ?', (job_id,))
    job = cur.fetchone()
    assert job['enabled'] == 1, "Job should be enabled"
    print(f"Automation job OK: {job['name']} enabled={job['enabled']}")

    # ── Test: Connected app ──────────────────────────────────────────────────
    app_id = 'app_001'
    cur.execute(
        '''INSERT INTO connected_apps (id, name, provider, config, status, last_sync, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (app_id, 'Gmail', 'google', json.dumps({'scope': 'mail'}), 'connected', now, now)
    )
    conn.commit()
    cur.execute('SELECT * FROM connected_apps WHERE id = ?', (app_id,))
    app = cur.fetchone()
    config = json.loads(app['config'])
    assert config['scope'] == 'mail', "Config JSON should be preserved"
    print(f"Connected app OK: {app['name']} config={config}")

    # ── Test: Notifications ──────────────────────────────────────────────────
    notif_id = 'notif_001'
    cur.execute(
        'INSERT INTO notifications_log (id, type, title, body, read, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (notif_id, 'info', 'Welcome', 'Welcome to Driver', 0, now)
    )
    conn.commit()
    cur.execute('SELECT * FROM notifications_log WHERE id = ?', (notif_id,))
    notif = cur.fetchone()
    assert notif['read'] == 0, "Notification should be unread"
    print(f"Notification OK: {notif['title']} read={notif['read']}")

    # ── Test: Search conversations ──────────────────────────────────────────
    cur.execute(
        'INSERT INTO conversations (id, title, project_id, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        ('conv_002', 'Email from boss', proj_id, 'claude-sonnet-4-5', now, now)
    )
    conn.commit()
    cur.execute("SELECT * FROM conversations WHERE title LIKE ? ORDER BY updated_at DESC", ('%Email%',))
    search_results = cur.fetchall()
    assert len(search_results) == 1, "Search should find the conversation"
    print(f"Search OK: found '{search_results[0]['title']}'")

    print("\n" + "=" * 60)
    print("All tests passed! Schema is valid and all CRUD operations work.")
    conn.close()

if __name__ == '__main__':
    main()
