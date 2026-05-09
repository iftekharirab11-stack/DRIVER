import { create } from 'zustand';

const initialIntegrations = [
  { id: 'google', name: 'Google Workspace', icon: '📧', status: 'disconnected', loading: false },
  { id: 'github', name: 'GitHub', icon: '🐙', status: 'disconnected', loading: false },
  { id: 'slack', name: 'Slack', icon: '💬', status: 'disconnected', loading: false },
  { id: 'notion', name: 'Notion', icon: '📝', status: 'disconnected', loading: false },
];

export const useIntegrationStore = create((set, get) => ({
  integrations: initialIntegrations,
  loading: false,
  error: null,

  setIntegrationStatus: (id, status) => set((state) => ({
    integrations: state.integrations.map((i) =>
      i.id === id ? { ...i, status, loading: false } : i
    )
  })),

  setIntegrationLoading: (id, val) => set((state) => ({
    integrations: state.integrations.map((i) =>
      i.id === id ? { ...i, loading: val } : i
    )
  })),

  connect: async (id) => {
    const { setIntegrationStatus, setIntegrationLoading } = get();
    setIntegrationLoading(id, true);
    try {
      // Backend call would go here
      setIntegrationStatus(id, 'connected');
    } catch (error) {
      set(state => ({
        integrations: state.integrations.map((i) =>
          i.id === id ? { ...i, loading: false, status: 'error' } : i
        ),
        error: error.message
      }));
    }
  },

  disconnect: async (id) => {
    const { setIntegrationStatus, setIntegrationLoading } = get();
    setIntegrationLoading(id, true);
    try {
      setIntegrationStatus(id, 'disconnected');
    } catch (error) {
      set(state => ({
        integrations: state.integrations.map((i) =>
          i.id === id ? { ...i, loading: false, status: 'error' } : i
        ),
        error: error.message
      }));
    }
  },

  reset: () => set({ integrations: initialIntegrations, loading: false, error: null }),
}));