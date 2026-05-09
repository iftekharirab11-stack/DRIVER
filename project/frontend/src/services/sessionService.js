import { useSessionStore } from '../store/sessionStore';
import { useChatStore } from '../store/chatStore';
import { useActivityStore, ACTIVITY_TYPES } from '../store/activityStore';
import { useMemoryStore } from '../store/memoryStore';

/**
 * Session service for handling session lifecycle and persistence
 */
export class SessionService {
  static initializeSession() {
    return new Promise(async (resolve, reject) => {
      try {
        // Initialize session
        const sessionId = await useSessionStore.getState().initSession();

        if (!sessionId) {
          throw new Error('Session initialization failed');
        }

        // Restore previous state if available
        this.restoreSessionState();

        // Add initialization activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: 'Driver AI session initialized successfully',
        });

        resolve(sessionId);
      } catch (error) {
        console.error('Session initialization error:', error);
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.ERROR,
          text: `Session initialization failed: ${error.message}`,
        });
        reject(error);
      }
    });
  }

  static restoreSessionState() {
    try {
      // Check if we have persisted chat messages
      const chatState = useChatStore.getState();
      if (chatState.messages.length > 0) {
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: `Restored ${chatState.messages.length} messages from previous session`,
        });
      }

      // Check if we have memory data
      const memoryState = useMemoryStore.getState();
      const memoryItems = Object.values(memoryState.memory).flat().filter(Boolean);
      if (memoryItems.length > 0) {
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.MEMORY,
          text: `Restored memory with ${memoryItems.length} items`,
        });
      }
    } catch (error) {
      console.error('Session restoration error:', error);
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.ERROR,
        text: `Failed to restore session: ${error.message}`,
      });
    }
  }

  static handleNetworkError(error) {
    const errorMessage = error.response?.data?.detail || error.message || 'Network error occurred';

    useActivityStore.getState().addActivity({
      type: ACTIVITY_TYPES.ERROR,
      text: `Network error: ${errorMessage}`,
    });

    // Show user-friendly error message
    useChatStore.getState().addMessage({
      id: Date.now(),
      role: 'assistant',
      content: `⚠️ Network issue detected: ${errorMessage}. Please check your connection.`,
      timestamp: new Date(),
    });

    return {
      error: errorMessage,
      timestamp: new Date(),
    };
  }

  static handleApiError(error) {
    const errorMessage = error.response?.data?.detail || error.message || 'API request failed';

    useActivityStore.getState().addActivity({
      type: ACTIVITY_TYPES.ERROR,
      text: `API error: ${errorMessage}`,
    });

    // Show user-friendly error message
    useChatStore.getState().addMessage({
      id: Date.now(),
      role: 'assistant',
      content: `❌ API error: ${errorMessage}. Please try again.`,
      timestamp: new Date(),
    });

    return {
      error: errorMessage,
      timestamp: new Date(),
    };
  }

  static cleanupSession() {
    try {
      // Clear session data
      useSessionStore.getState().logout();

      // Add cleanup activity
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.SYSTEM,
        text: 'Session cleaned up successfully',
      });
    } catch (error) {
      console.error('Session cleanup error:', error);
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.ERROR,
        text: `Session cleanup failed: ${error.message}`,
      });
    }
  }

  static checkSessionHealth() {
    const sessionState = useSessionStore.getState();
    const chatState = useChatStore.getState();

    if (!sessionState.sessionId) {
      throw new Error('No active session');
    }

    if (chatState.error) {
      throw new Error(`Session has errors: ${chatState.error}`);
    }

    return {
      healthy: true,
      sessionId: sessionState.sessionId,
      messageCount: chatState.messages.length,
      isThinking: chatState.isThinking,
    };
  }
}