import { create } from 'zustand';
import storageManager from '../desktop/storage';
import { isElectron } from '../electron';

export const useDesktopSessionStore = create((set, get) => ({
  // Local sessions
  localSessions: {},
  currentSession: null,

  // Initialize from storage
  initialize: async () => {
    try {
      const sessions = await storageManager.getAllSessions();
      const preferences = await storageManager.getPreferences();

      set({
        localSessions: sessions,
        preferences: preferences
      });

      // Load most recent session if available
      const sessionIds = Object.keys(sessions);
      if (sessionIds.length > 0) {
        const mostRecentSessionId = sessionIds[0]; // Simple approach for now
        const session = await storageManager.getSession(mostRecentSessionId);
        set({ currentSession: session });
      }
    } catch (error) {
      console.error('Failed to initialize desktop sessions:', error);
    }
  },

  // Load session from local storage
  loadLocalSession: async (sessionId) => {
    try {
      const session = await storageManager.getSession(sessionId);
      if (session) {
        set({ currentSession: session });
        return session;
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
    return null;
  },

  // Save session to local storage
  saveLocalSession: async (sessionId, sessionData) => {
    try {
      await storageManager.saveSession(sessionId, sessionData);
      set(state => ({
        localSessions: {
          ...state.localSessions,
          [sessionId]: sessionData
        },
        currentSession: sessionData
      }));
      return true;
    } catch (error) {
      console.error('Failed to save session:', error);
      return false;
    }
  },

  // Create new local session
  createLocalSession: async (name = 'New Session') => {
    try {
      const sessionId = `local-${Date.now()}`;
      const newSession = {
        id: sessionId,
        name: name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        history: [],
        files: [],
        preferences: get().preferences || {}
      };

      await storageManager.saveSession(sessionId, newSession);
      set(state => ({
        localSessions: {
          ...state.localSessions,
          [sessionId]: newSession
        },
        currentSession: newSession
      }));

      return sessionId;
    } catch (error) {
      console.error('Failed to create session:', error);
      return null;
    }
  },

  // Delete local session
  deleteLocalSession: async (sessionId) => {
    try {
      await storageManager.saveSession(sessionId, null); // Remove from storage
      set(state => {
        const newSessions = {...state.localSessions};
        delete newSessions[sessionId];
        return {
          localSessions: newSessions,
          currentSession: state.currentSession?.id === sessionId ? null : state.currentSession
        };
      });
      return true;
    } catch (error) {
      console.error('Failed to delete session:', error);
      return false;
    }
  },

  // Add message to current session history
  addMessageToHistory: async (message) => {
    try {
      const currentSession = get().currentSession;
      if (!currentSession) return false;

      const updatedSession = {
        ...currentSession,
        history: [...currentSession.history, message],
        updatedAt: new Date().toISOString()
      };

      await storageManager.saveSession(currentSession.id, updatedSession);
      set({ currentSession: updatedSession });
      return true;
    } catch (error) {
      console.error('Failed to add message to history:', error);
      return false;
    }
  },

  // Add file to current workspace
  addFileToWorkspace: async (file) => {
    try {
      const currentSession = get().currentSession;
      if (!currentSession) return false;

      // Check if file already exists
      const fileExists = currentSession.files.some(f => f.fileId === file.fileId);
      if (fileExists) return true;

      const updatedSession = {
        ...currentSession,
        files: [...currentSession.files, file],
        updatedAt: new Date().toISOString()
      };

      await storageManager.saveSession(currentSession.id, updatedSession);
      set({ currentSession: updatedSession });

      // Add to recent files
      if (file.path) {
        await storageManager.addRecentFile(file.path);
      }

      return true;
    } catch (error) {
      console.error('Failed to add file to workspace:', error);
      return false;
    }
  },

  // Update preferences
  updatePreferences: async (newPreferences) => {
    try {
      const currentSession = get().currentSession;
      if (currentSession) {
        const updatedSession = {
          ...currentSession,
          preferences: {
            ...currentSession.preferences,
            ...newPreferences
          }
        };

        await storageManager.saveSession(currentSession.id, updatedSession);
        set({ currentSession: updatedSession });
      }

      await storageManager.savePreferences(newPreferences);
      set(state => ({
        preferences: {
          ...state.preferences,
          ...newPreferences
        }
      }));

      return true;
    } catch (error) {
      console.error('Failed to update preferences:', error);
      return false;
    }
  },

  // Sync with backend when available
  syncWithBackend: async () => {
    if (!isElectron()) return false;

    try {
      const sessions = get().localSessions;
      for (const sessionId in sessions) {
        const session = sessions[sessionId];
        // Implement backend sync logic here
        console.log(`Would sync session ${sessionId} with backend`);
      }
      return true;
    } catch (error) {
      console.error('Failed to sync with backend:', error);
      return false;
    }
  },

  // Clear all local data
  clearAllData: async () => {
    try {
      await storageManager.clearAllData();
      set({
        localSessions: {},
        currentSession: null,
        preferences: {
          theme: 'dark',
          fontSize: 14,
          autoStartBackend: true
        }
      });
      return true;
    } catch (error) {
      console.error('Failed to clear all data:', error);
      return false;
    }
  }
}));
// Initialize on store creation
useDesktopSessionStore.getState().initialize();