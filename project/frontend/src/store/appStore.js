import { create } from 'zustand';

export const useAppStore = create((set) => ({
  // Active tab/route management
  activeTab: 'chat',
  sessionError: null,
  isLoading: false,

  // Set active tab
  setActiveTab: (tab) => set({ activeTab: tab, sessionError: null }),

  // Set loading state
  setLoading: (loading) => set({ isLoading: loading }),

  // Set session error
  setSessionError: (error) => set({ sessionError: error }),

  // Clear session error
  clearSessionError: () => set({ sessionError: null }),

  // Reset app state
  reset: () => set({
    activeTab: 'chat',
    sessionError: null,
    isLoading: false
  })
}));