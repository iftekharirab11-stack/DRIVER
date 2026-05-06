import { create } from 'zustand';

export const useTaskStore = create((set, get) => ({
  tasks: {},
  activeJobs: {},
  loading: false,
  error: null,

  addTask: (task) => set((state) => ({
    tasks: { ...state.tasks, [task.id]: task }
  })),

  updateTask: (id, updates) => set((state) => ({
    tasks: { ...state.tasks, [id]: { ...state.tasks[id], ...updates } }
  })),

  removeTask: (id) => set((state) => {
    const { [id]: _, ...rest } = state.tasks;
    return { tasks: rest };
  }),

  setActiveJobs: (jobs) => set({ activeJobs: jobs }),

  setLoading: (val) => set({ loading: val }),

  setError: (error) => set({ error }),

  reset: () => set({ tasks: {}, activeJobs: {}, loading: false, error: null }),
}));