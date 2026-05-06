import { create } from 'zustand';
import { createSession, getSession, clearSession } from '../api/auth';
import { sendMessage, getDashboard, streamUpdates } from '../api/chat';
import { useChatStore } from './chatStore';
import { useTaskStore } from './taskStore';

export const useSessionStore = create((set, get) => ({
  sessionId: getSession(),
  connectionStatus: null,
  sseConnected: false,
  pollInterval: null,

  initSession: async () => {
    try {
      const sessionId = await createSession();
      set({ sessionId });

      useChatStore.getState().addActivity({ type: 'system', text: 'Session initialized' });

      const unsub = streamUpdates(sessionId, (data) => {
        if (data.system) {
          set({ connectionStatus: data.system, sseConnected: true });
        }
      });

      set((state) => ({ pollInterval: window.setInterval(() => {
        get().loadDashboard();
      }, 5000) }));

      get().loadDashboard();
      return sessionId;
    } catch (error) {
      console.error('Session init failed:', error);
      set({ sseConnected: false });
      useChatStore.getState().addActivity({ type: 'error', text: `Session init failed: ${error.message}` });
      return null;
    }
  },

  loadDashboard: async () => {
    try {
      const data = await getDashboard();
      set({ connectionStatus: data.system || {} });
      return data;
    } catch (error) {
      console.error('Dashboard error:', error);
    }
  },

  sendUserMessage: async (text) => {
    const sessionId = get().sessionId;
    if (!sessionId || !text?.trim()) return;

    useChatStore.getState().addActivity({ type: 'user', text });
    useChatStore.getState().setThinking(true);
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    useChatStore.getState().addMessage(userMessage);

    try {
      const response = await sendMessage(sessionId, text.trim());
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      useChatStore.getState().addMessage(aiMessage);
      useChatStore.getState().addActivity({ type: 'update', text: 'Response received' });

      if (response.job_status) {
        useTaskStore.setState({ activeJobs: response.job_status.active_jobs || {} });
      }
    } catch (error) {
      useChatStore.getState().addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      });
      useChatStore.getState().addActivity({ type: 'error', text: error.message });
    } finally {
      useChatStore.getState().setThinking(false);
    }
  },

  logout: () => {
    const { pollInterval } = get();
    if (pollInterval) clearInterval(pollInterval);
    clearSession();
    set({ sessionId: null, connectionStatus: null, sseConnected: false });
    useChatStore.getState().reset();
    useTaskStore.getState().reset();
  },
}));