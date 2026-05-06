import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useChatStore = create(
  persist(
    (set, get) => ({
      messages: [],
      activities: [],
      isThinking: false,
      error: null,

      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),

      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map((m) => 
          m.id === id ? { ...m, ...updates } : m
        )
      })),

      addActivity: (activity) => set((state) => ({
        activities: [...state.activities, { ...activity, id: Date.now(), timestamp: new Date() }].slice(-100)
      })),

      clearMessages: () => set({ messages: [] }),

      setThinking: (val) => set({ isThinking: val }),

      setError: (error) => set({ error }),

      reset: () => set({ 
        messages: [], 
        activities: [],
        isThinking: false, 
        error: null 
      }),
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({ messages: state.messages }),
    }
  )
);