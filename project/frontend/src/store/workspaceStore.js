import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useActivityStore, ACTIVITY_TYPES } from './activityStore';
import { useChatStore } from './chatStore';
import { useMemoryStore } from './memoryStore';
import { useContextStore } from './contextStore';

export const useWorkspaceStore = create(
  persist(
    (set, get) => ({
      // Current active workspace
      currentWorkspace: null,

      // Available workspaces
      workspaces: [],

      // Initialize with default workspace
      initializeWorkspaces: () => {
        const defaultWorkspace = {
          id: 'default',
          name: 'Personal',
          description: 'Your personal workspace',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          memory: {},
          files: [],
          conversations: [],
          settings: {
            theme: 'dark',
            notifications: true
          }
        };

        set({
          currentWorkspace: defaultWorkspace,
          workspaces: [defaultWorkspace]
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: 'Initialized personal workspace'
        });

        return defaultWorkspace;
      },

      // Create a new workspace
      createWorkspace: (workspaceData) => {
        const { workspaces } = get();

        if (workspaces.some(ws => ws.name === workspaceData.name)) {
          throw new Error('Workspace with this name already exists');
        }

        const newWorkspace = {
          id: `ws_${Date.now()}`,
          name: workspaceData.name,
          description: workspaceData.description || '',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          memory: {},
          files: [],
          conversations: [],
          settings: {
            theme: 'dark',
            notifications: true,
            ...workspaceData.settings
          }
        };

        set({
          workspaces: [...workspaces, newWorkspace]
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: `Created new workspace: ${newWorkspace.name}`
        });

        return newWorkspace;
      },

      // Switch to a different workspace
      switchWorkspace: (workspaceId) => {
        const { workspaces, currentWorkspace } = get();

        // Check if workspace exists
        const targetWorkspace = workspaces.find(ws => ws.id === workspaceId);
        if (!targetWorkspace) {
          throw new Error('Workspace not found');
        }

        // Save current workspace state
        if (currentWorkspace) {
          this.saveWorkspaceState(currentWorkspace.id);
        }

        set({
          currentWorkspace: targetWorkspace
        });

        // Load workspace state
        this.loadWorkspaceState(targetWorkspace.id);

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: `Switched to workspace: ${targetWorkspace.name}`
        });

        return targetWorkspace;
      },

      // Save workspace state (memory, files, conversations)
      saveWorkspaceState: (workspaceId) => {
        const { currentWorkspace } = get();

        if (!currentWorkspace || currentWorkspace.id !== workspaceId) {
          return;
        }

        // Save current state to workspace
        const updatedWorkspace = {
          ...currentWorkspace,
          memory: useMemoryStore.getState().memory,
          files: this.getCurrentFiles(),
          conversations: this.getCurrentConversations(),
          updatedAt: new Date().toISOString()
        };

        set((state) => ({
          workspaces: state.workspaces.map(ws =>
            ws.id === workspaceId ? updatedWorkspace : ws
          )
        }));
      },

      // Load workspace state
      loadWorkspaceState: (workspaceId) => {
        const { workspaces } = get();
        const workspace = workspaces.find(ws => ws.id === workspaceId);

        if (!workspace) {
          throw new Error('Workspace not found');
        }

        // Load memory
        useMemoryStore.getState().updateMemory(workspace.memory || {});

        // Load files (would be handled by file system in real implementation)
        // Load conversations (would be handled by chat system)

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: `Loaded workspace: ${workspace.name}`
        });
      },

      // Add file to current workspace
      addFileToWorkspace: (fileData) => {
        const { currentWorkspace } = get();

        if (!currentWorkspace) {
          throw new Error('No active workspace');
        }

        set({
          currentWorkspace: {
            ...currentWorkspace,
            files: [...currentWorkspace.files, fileData],
            updatedAt: new Date().toISOString()
          }
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.UPLOAD,
          text: `Added file to workspace: ${fileData.fileName}`
        });

        return currentWorkspace.files;
      },

      // Remove file from current workspace
      removeFileFromWorkspace: (fileId) => {
        const { currentWorkspace } = get();

        if (!currentWorkspace) {
          throw new Error('No active workspace');
        }

        set({
          currentWorkspace: {
            ...currentWorkspace,
            files: currentWorkspace.files.filter(file => file.fileId !== fileId),
            updatedAt: new Date().toISOString()
          }
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: 'Removed file from workspace'
        });

        return currentWorkspace.files;
      },

      // Get files in current workspace
      getCurrentFiles: () => {
        const { currentWorkspace } = get();
        return currentWorkspace?.files || [];
      },

      // Get conversations in current workspace
      getCurrentConversations: () => {
        const { currentWorkspace } = get();
        return currentWorkspace?.conversations || [];
      },

      // Update workspace settings
      updateWorkspaceSettings: (settings) => {
        const { currentWorkspace } = get();

        if (!currentWorkspace) {
          throw new Error('No active workspace');
        }

        set({
          currentWorkspace: {
            ...currentWorkspace,
            settings: {
              ...currentWorkspace.settings,
              ...settings
            },
            updatedAt: new Date().toISOString()
          }
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: 'Updated workspace settings'
        });

        return currentWorkspace.settings;
      },

      // Delete a workspace
      deleteWorkspace: (workspaceId) => {
        const { workspaces, currentWorkspace } = get();

        if (workspaces.length <= 1) {
          throw new Error('Cannot delete the last workspace');
        }

        if (currentWorkspace?.id === workspaceId) {
          throw new Error('Cannot delete active workspace. Switch first.');
        }

        const updatedWorkspaces = workspaces.filter(ws => ws.id !== workspaceId);

        set({
          workspaces: updatedWorkspaces
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: 'Deleted workspace'
        });

        return updatedWorkspaces;
      },

      // Get workspace by ID
      getWorkspace: (workspaceId) => {
        const { workspaces } = get();
        return workspaces.find(ws => ws.id === workspaceId);
      },

      // Export workspace data
      exportWorkspace: (workspaceId) => {
        const { workspaces } = get();
        const workspace = workspaces.find(ws => ws.id === workspaceId);

        if (!workspace) {
          throw new Error('Workspace not found');
        }

        // Create export data (simplified for demo)
        const exportData = {
          workspace: {
            ...workspace,
            // Remove sensitive data
            memory: undefined,
            files: workspace.files.map(file => ({
              fileId: file.fileId,
              fileName: file.fileName,
              fileType: file.fileType,
              fileSize: file.fileSize
            }))
          },
          exportedAt: new Date().toISOString()
        };

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.SYSTEM,
          text: `Exported workspace: ${workspace.name}`
        });

        return exportData;
      }
    }),
    {
      name: 'workspace-storage',
      partialize: (state) => ({
        currentWorkspace: state.currentWorkspace,
        workspaces: state.workspaces
      }),
    }
  )
);

// Helper functions for workspace management
export const WorkspaceHelper = {
  createDefaultWorkspace: () => ({
    id: 'default',
    name: 'Personal',
    description: 'Your personal workspace',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    memory: {},
    files: [],
    conversations: [],
    settings: {
      theme: 'dark',
      notifications: true
    }
  }),

  generateWorkspaceId: () => `ws_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,

  validateWorkspaceName: (name) => {
    if (!name || name.trim().length === 0) {
      throw new Error('Workspace name cannot be empty');
    }

    if (name.length > 50) {
      throw new Error('Workspace name too long (max 50 characters)');
    }

    return name.trim();
  }
};