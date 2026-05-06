/**
 * Demo script for the Driver database layer.
 * Run: npm run test (or node dist/test-db.js) after building.
 *
 * Prerequisites:
 * - better-sqlite3 native addon compiled successfully (run npm install without --ignore-scripts on a machine with build tools)
 */

import db from './main/db/database';
import * as queries from './main/db/queries';

console.log('🚀 Driver DB Demo\n');

// Clean slate for demo
db.prepare('DELETE FROM messages').run();
db.prepare('DELETE FROM conversations').run();
db.prepare('DELETE FROM projects').run();

// ── Projects ─────────────────────────────────────────────────────
const work = queries.createProject({ name: 'Work', color: '#3B82F6' });
const personal = queries.createProject({ name: 'Personal', color: '#10B981' });
const research = queries.createProject({ name: 'Research', color: '#F59E0B' });

console.log(`✅ Created projects: ${work.name}, ${personal.name}, ${research.name}`);

// ── Conversations ─────────────────────────────────────────────────
const conv1 = queries.createConversation({
  title: 'Show my GitHub repos',
  project_id: work.id,
  model: 'claude-sonnet-4-5',
});
const conv2 = queries.createConversation({
  title: 'Read latest emails',
  project_id: personal.id,
  model: 'claude-sonnet-4-5',
});
const conv3 = queries.createConversation({
  title: 'List Drive files',
  project_id: research.id,
});

console.log(`✅ Created conversations: "${conv1.title}", "${conv2.title}", "${conv3.title}"`);

// ── Messages ─────────────────────────────────────────────────────
queries.createMessage({
  conversation_id: conv1.id,
  role: 'user',
  content: 'Show my GitHub repos',
});
queries.createMessage({
  conversation_id: conv1.id,
  role: 'assistant',
  content: 'Found 3 repositories',
});
queries.createMessage({
  conversation_id: conv2.id,
  role: 'user',
  content: 'Read latest emails',
});
queries.createMessage({
  conversation_id: conv2.id,
  role: 'assistant',
  content: 'Found 5 unread emails',
});
queries.createMessage({
  conversation_id: conv3.id,
  role: 'user',
  content: 'List Drive files',
});

console.log('✅ Added messages to conversations');

// ── Fetch & display ──────────────────────────────────────────────
console.log('\n📋 Projects:');
queries.getAllProjects().forEach((p) => {
  console.log(`  • ${p.name} (${p.id}) – ${p.color}`);
});

console.log('\n💬 Conversations (most recent first):');
queries.getAllConversations().forEach((c) => {
  const messages = queries.getMessagesByConversation(c.id);
  console.log(`  • [${c.id.slice(0, 8)}...] ${c.title} – ${messages.length} messages`);
});

console.log('\n🔍 Search "email":');
const results = queries.searchConversations('email');
results.forEach((c) => console.log(`  found: ${c.title}`));

console.log('\n🎉 Demo completed successfully!');
