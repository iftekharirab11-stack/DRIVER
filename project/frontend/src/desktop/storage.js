/**
 * Local-First Storage System
 * Works in both Electron and web environments
 */

class LocalStorageManager {
  constructor() {
    this.storage = this._getStorageImplementation();
  }

  _getStorageImplementation() {
    // Try Electron storage first
    if (window && window.electronAPI) {
      try {
        return {
          type: 'electron',
          getItem: async (key) => {
            return await window.electronAPI.getLocalData(key);
          },
          setItem: async (key, value) => {
            await window.electronAPI.setLocalData(key, value);
          },
          removeItem: async (key) => {
            await window.electronAPI.removeLocalData(key);
          }
        };
      } catch (error) {
        console.warn('Electron storage failed, falling back to localStorage:', error);
      }
    }

    // Fall back to web localStorage
    return {
      type: 'web',
      getItem: async (key) => {
        const value = localStorage.getItem(key);
        try {
          return value ? JSON.parse(value) : null;
        } catch {
          return value;
        }
      },
      setItem: async (key, value) => {
        if (typeof value === 'object') {
          localStorage.setItem(key, JSON.stringify(value));
        } else {
          localStorage.setItem(key, value);
        }
      },
      removeItem: async (key) => {
        localStorage.removeItem(key);
      }
    };
  }

  // Session management
  async getSession(sessionId) {
    return await this.storage.getItem(`sessions.${sessionId}`);
  }

  async saveSession(sessionId, sessionData) {
    await this.storage.setItem(`sessions.${sessionId}`, sessionData);
  }

  async getAllSessions() {
    if (this.storage.type === 'electron') {
      // In Electron, we need to get all sessions
      const sessions = {};
      // This would need to be implemented in the Electron backend
      // For now, return empty object
      return sessions;
    } else {
      // In web, scan localStorage for session keys
      const sessions = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('sessions.')) {
          const sessionId = key.replace('sessions.', '');
          sessions[sessionId] = await this.getSession(sessionId);
        }
      }
      return sessions;
    }
  }

  // Workspace management
  async getWorkspaces() {
    const workspaces = await this.storage.getItem('workspaces') || {};
    return workspaces;
  }

  async saveWorkspace(workspaceId, workspaceData) {
    const workspaces = await this.getWorkspaces();
    workspaces[workspaceId] = workspaceData;
    await this.storage.setItem('workspaces', workspaces);
  }

  // Preferences
  async getPreferences() {
    return await this.storage.getItem('preferences') || {
      theme: 'dark',
      fontSize: 14,
      autoStartBackend: true
    };
  }

  async savePreferences(preferences) {
    await this.storage.setItem('preferences', preferences);
  }

  // History
  async getHistory() {
    return await this.storage.getItem('history') || [];
  }

  async addHistoryItem(item) {
    const history = await this.getHistory();
    history.unshift(item);
    // Keep last 100 items
    const limitedHistory = history.slice(0, 100);
    await this.storage.setItem('history', limitedHistory);
  }

  // Recent files
  async getRecentFiles() {
    return await this.storage.getItem('recentFiles') || [];
  }

  async addRecentFile(filePath) {
    const recentFiles = await this.getRecentFiles();
    // Remove if already exists
    const index = recentFiles.indexOf(filePath);
    if (index !== -1) {
      recentFiles.splice(index, 1);
    }
    // Add to beginning
    recentFiles.unshift(filePath);
    // Keep last 20 files
    const limitedFiles = recentFiles.slice(0, 20);
    await this.storage.setItem('recentFiles', limitedFiles);
  }

  // Clear all data
  async clearAllData() {
    if (this.storage.type === 'electron') {
      // Would need Electron backend implementation
      console.warn('clearAllData not fully implemented for Electron');
    } else {
      localStorage.clear();
    }
  }
}

// Singleton instance
const storageManager = new LocalStorageManager();
export default storageManager;