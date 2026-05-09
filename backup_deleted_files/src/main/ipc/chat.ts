import { ipcMain, IpcMainEvent } from 'electron';
import * as dbQueries from '../db/queries';

/**
 * Register all IPC handlers for database operations.
 * Call this from your Electron main process after `app.whenReady()`.
 */
export function registerDatabaseIpcHandlers(): void {
  // ── Conversations ──────────────────────────────────────────────────────────
  ipcMain.handle('db:conversations:getAll', () => dbQueries.getAllConversations());
  ipcMain.handle('db:conversations:getById', (_: IpcMainEvent, id: string) => dbQueries.getConversationById(id));
  ipcMain.handle('db:conversations:getByProject', (_: IpcMainEvent, projectId: string | null) =>
    dbQueries.getConversationsByProject(projectId)
  );
  ipcMain.handle('db:conversations:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createConversation>[0]) =>
    dbQueries.createConversation(data)
  );
  ipcMain.handle('db:conversations:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateConversation>[1]) =>
    dbQueries.updateConversation(id, data)
  );
  ipcMain.handle('db:conversations:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteConversation(id));
  ipcMain.handle('db:conversations:search', (_: IpcMainEvent, query: string) => dbQueries.searchConversations(query));

  // ── Messages ───────────────────────────────────────────────────────────────
  ipcMain.handle('db:messages:getAll', () => dbQueries.getAllMessages());
  ipcMain.handle('db:messages:getByConversation', (_: IpcMainEvent, conversationId: string) =>
    dbQueries.getMessagesByConversation(conversationId)
  );
  ipcMain.handle('db:messages:getById', (_: IpcMainEvent, id: string) => dbQueries.getMessageById(id));
  ipcMain.handle('db:messages:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createMessage>[0]) =>
    dbQueries.createMessage(data)
  );
  ipcMain.handle('db:messages:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateMessage>[1]) =>
    dbQueries.updateMessage(id, data)
  );
  ipcMain.handle('db:messages:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteMessage(id));
  ipcMain.handle('db:messages:deleteByConversation', (_: IpcMainEvent, conversationId: string) =>
    dbQueries.deleteMessagesByConversation(conversationId)
  );

  // ── Projects ────────────────────────────────────────────────────────────────
  ipcMain.handle('db:projects:getAll', () => dbQueries.getAllProjects());
  ipcMain.handle('db:projects:getById', (_: IpcMainEvent, id: string) => dbQueries.getProjectById(id));
  ipcMain.handle('db:projects:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createProject>[0]) =>
    dbQueries.createProject(data)
  );
  ipcMain.handle('db:projects:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateProject>[1]) =>
    dbQueries.updateProject(id, data)
  );
  ipcMain.handle('db:projects:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteProject(id));

  // ── Memory ──────────────────────────────────────────────────────────────────
  ipcMain.handle('db:memory:getAll', () => dbQueries.getAllMemory());
  ipcMain.handle('db:memory:getById', (_: IpcMainEvent, id: string) => dbQueries.getMemoryById(id));
  ipcMain.handle('db:memory:getByType', (_: IpcMainEvent, type: string) => dbQueries.getMemoryByType(type));
  ipcMain.handle('db:memory:search', (_: IpcMainEvent, query: string) => dbQueries.searchMemory(query));
  ipcMain.handle('db:memory:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createMemory>[0]) =>
    dbQueries.createMemory(data)
  );
  ipcMain.handle('db:memory:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateMemory>[1]) =>
    dbQueries.updateMemory(id, data)
  );
  ipcMain.handle('db:memory:incrementAccess', (_: IpcMainEvent, id: string) => dbQueries.incrementMemoryAccess(id));
  ipcMain.handle('db:memory:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteMemory(id));

  // ── Automation Jobs ─────────────────────────────────────────────────────────
  ipcMain.handle('db:automation:getAll', () => dbQueries.getAllAutomationJobs());
  ipcMain.handle('db:automation:getById', (_: IpcMainEvent, id: string) => dbQueries.getAutomationJobById(id));
  ipcMain.handle('db:automation:getEnabled', () => dbQueries.getEnabledAutomationJobs());
  ipcMain.handle('db:automation:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createAutomationJob>[0]) =>
    dbQueries.createAutomationJob(data)
  );
  ipcMain.handle('db:automation:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateAutomationJob>[1]) =>
    dbQueries.updateAutomationJob(id, data)
  );
  ipcMain.handle('db:automation:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteAutomationJob(id));

  // ── Connected Apps ──────────────────────────────────────────────────────────
  ipcMain.handle('db:apps:getAll', () => dbQueries.getAllConnectedApps());
  ipcMain.handle('db:apps:getById', (_: IpcMainEvent, id: string) => dbQueries.getConnectedAppById(id));
  ipcMain.handle('db:apps:getByProvider', (_: IpcMainEvent, provider: string) => dbQueries.getConnectedAppsByProvider(provider));
  ipcMain.handle('db:apps:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createConnectedApp>[0]) =>
    dbQueries.createConnectedApp(data)
  );
  ipcMain.handle('db:apps:update', (_: IpcMainEvent, id: string, data: Parameters<typeof dbQueries.updateConnectedApp>[1]) =>
    dbQueries.updateConnectedApp(id, data)
  );
  ipcMain.handle('db:apps:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteConnectedApp(id));

  // ── Notifications ───────────────────────────────────────────────────────────
  ipcMain.handle('db:notifications:getAll', () => dbQueries.getAllNotifications());
  ipcMain.handle('db:notifications:getUnread', () => dbQueries.getUnreadNotifications());
  ipcMain.handle('db:notifications:getById', (_: IpcMainEvent, id: string) => dbQueries.getNotificationById(id));
  ipcMain.handle('db:notifications:create', (_: IpcMainEvent, data: Parameters<typeof dbQueries.createNotification>[0]) =>
    dbQueries.createNotification(data)
  );
  ipcMain.handle('db:notifications:markRead', (_: IpcMainEvent, id: string, read?: boolean) =>
    dbQueries.markNotificationRead(id, read)
  );
  ipcMain.handle('db:notifications:markAllRead', () => dbQueries.markAllNotificationsRead());
  ipcMain.handle('db:notifications:delete', (_: IpcMainEvent, id: string) => dbQueries.deleteNotification(id));
}
