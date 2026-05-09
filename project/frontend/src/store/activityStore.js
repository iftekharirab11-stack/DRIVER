import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useActivityStore = create(
  persist(
    (set, get) => ({
      // Activity feed items
      activities: [],

      // Add a new activity to the feed
      addActivity: (activity) => set((state) => ({
        activities: [
          {
            ...activity,
            id: Date.now(),
            timestamp: new Date()
          },
          ...state.activities
        ].slice(0, 100) // Keep maximum 100 activities
      })),

      // Clear all activities
      clearActivity: () => set({ activities: [] }),

      // Stream activity updates (for real-time updates)
      streamActivity: (activityData) => {
        const activity = {
          ...activityData,
          id: Date.now(),
          timestamp: new Date()
        };
        set((state) => ({
          activities: [activity, ...state.activities].slice(0, 100)
        }));
      },

      // Add system activity
      addSystemActivity: (text, type = 'system') => set((state) => ({
        activities: [
          {
            id: Date.now(),
            type,
            text,
            timestamp: new Date()
          },
          ...state.activities
        ].slice(0, 100)
      })),

      // Add multiple activities at once
      addMultipleActivities: (newActivities) => set((state) => ({
        activities: [
          ...newActivities.map(activity => ({
            ...activity,
            id: Date.now() + Math.random(), // Ensure unique IDs
            timestamp: new Date()
          })),
          ...state.activities
        ].slice(0, 100)
      })),

      // Get recent activities (last N items)
      getRecentActivities: (count = 10) => {
        const state = get();
        return state.activities.slice(0, count);
      }
    }),
    {
      name: 'activity-storage',
      partialize: (state) => ({ activities: state.activities }),
    }
  )
);

// Activity types for consistent usage
export const ACTIVITY_TYPES = {
  SYSTEM: 'system',
  USER: 'user',
  SUCCESS: 'success',
  ERROR: 'error',
  LOADING: 'loading',
  UPDATE: 'update',
  UPLOAD: 'upload',
  MEMORY: 'memory',
  THINKING: 'thinking',
  RESPONSE: 'response'
};

// Helper function to create standardized activity objects
export const createActivity = (type, text, additionalData = {}) => ({
  type,
  text,
  ...additionalData
});