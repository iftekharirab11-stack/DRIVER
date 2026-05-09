import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useMemoryStore = create(
  persist(
    (set, get) => ({
      // Memory data
      memory: {
        username: null,
        recentTasks: [],
        projectNames: [],
        previousTopics: [],
        preferences: {},
      },

      // Save memory data
      saveMemory: (key, value) => set((state) => ({
        memory: {
          ...state.memory,
          [key]: value
        }
      })),

      // Get specific memory value
      getMemory: (key) => {
        const state = get();
        return state.memory[key];
      },

      // Update memory with new data
      updateMemory: (updates) => set((state) => ({
        memory: {
          ...state.memory,
          ...updates
        }
      })),

      // Add to array-based memory (like recent tasks)
      addToMemoryArray: (key, item) => set((state) => ({
        memory: {
          ...state.memory,
          [key]: [...(state.memory[key] || []), item].slice(-10) // Keep last 10 items
        }
      })),

      // Clear specific memory
      clearMemory: (key) => set((state) => ({
        memory: {
          ...state.memory,
          [key]: key === 'preferences' ? {} : null
        }
      })),

      // Reset all memory
      resetMemory: () => set({
        memory: {
          username: null,
          recentTasks: [],
          projectNames: [],
          previousTopics: [],
          preferences: {},
        }
      }),
    }),
    {
      name: 'memory-storage',
      partialize: (state) => ({ memory: state.memory }),
    }
  )
);

// Helper function to get memory summary for AI context
export const getMemoryContext = () => {
  const state = useMemoryStore.getState();
  const { memory } = state;

  const contextParts = [];

  if (memory.username) {
    contextParts.push(`User name: ${memory.username}`);
  }

  if (memory.recentTasks && memory.recentTasks.length > 0) {
    contextParts.push(`Recent tasks: ${memory.recentTasks.slice(-3).join(', ')}`);
  }

  if (memory.projectNames && memory.projectNames.length > 0) {
    contextParts.push(`Active projects: ${memory.projectNames.join(', ')}`);
  }

  if (memory.previousTopics && memory.previousTopics.length > 0) {
    contextParts.push(`Previous topics: ${memory.previousTopics.slice(-2).join(', ')}`);
  }

  return contextParts.length > 0
    ? `Memory context: ${contextParts.join('. ')}.`
    : 'No memory context available.';
};