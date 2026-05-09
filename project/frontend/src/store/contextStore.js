import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useActivityStore, ACTIVITY_TYPES } from './activityStore';
import { useChatStore } from './chatStore';

export const useContextStore = create(
  persist(
    (set, get) => ({
      // Attached conversations for context
      attachedConversations: [],

      // Available conversations for attachment
      availableConversations: [],

      // Attach a conversation to current context
      attachConversation: (conversationId) => {
        const { attachedConversations, availableConversations } = get();

        // Check if conversation exists and isn't already attached
        const conversationToAttach = availableConversations.find(
          conv => conv.id === conversationId
        );

        if (!conversationToAttach) {
          throw new Error('Conversation not found');
        }

        if (attachedConversations.some(conv => conv.id === conversationId)) {
          throw new Error('Conversation already attached');
        }

        const updatedAttached = [...attachedConversations, conversationToAttach];
        const updatedAvailable = availableConversations.filter(
          conv => conv.id !== conversationId
        );

        set({
          attachedConversations: updatedAttached,
          availableConversations: updatedAvailable
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.CONTEXT,
          text: `Attached conversation: ${conversationToAttach.title || 'Untitled'}`
        });

        return updatedAttached;
      },

      // Remove an attached conversation
      removeConversation: (conversationId) => {
        const { attachedConversations, availableConversations } = get();

        const conversationToRemove = attachedConversations.find(
          conv => conv.id === conversationId
        );

        if (!conversationToRemove) {
          throw new Error('Attached conversation not found');
        }

        const updatedAttached = attachedConversations.filter(
          conv => conv.id !== conversationId
        );
        const updatedAvailable = [...availableConversations, conversationToRemove];

        set({
          attachedConversations: updatedAttached,
          availableConversations: updatedAvailable
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.CONTEXT,
          text: `Removed attached conversation: ${conversationToRemove.title || 'Untitled'}`
        });

        return updatedAttached;
      },

      // Get merged context from all attached conversations
      getMergedContext: () => {
        const { attachedConversations } = get();
        const { messages: currentMessages } = useChatStore.getState();

        // Get messages from attached conversations
        const attachedMessages = attachedConversations.flatMap(conv =>
          conv.messages || []
        );

        // Combine with current conversation (excluding system messages)
        const allMessages = [
          ...attachedMessages.filter(msg => msg.role !== 'system'),
          ...currentMessages.filter(msg => msg.role !== 'system')
        ];

        return {
          messages: allMessages,
          conversationCount: attachedConversations.length,
          totalMessages: allMessages.length
        };
      },

      // Clear all attached conversations
      clearAttachedConversations: () => {
        const { attachedConversations, availableConversations } = get();

        if (attachedConversations.length === 0) {
          return [];
        }

        // Move all attached conversations back to available
        const allAvailable = [...availableConversations, ...attachedConversations];

        set({
          attachedConversations: [],
          availableConversations: allAvailable
        });

        // Add activity
        useActivityStore.getState().addActivity({
          type: ACTIVITY_TYPES.CONTEXT,
          text: `Cleared all ${attachedConversations.length} attached conversations`
        });

        return [];
      },

      // Add a conversation to available list
      addAvailableConversation: (conversation) => {
        set((state) => ({
          availableConversations: [...state.availableConversations, conversation]
        }));
      },

      // Remove a conversation from available list
      removeAvailableConversation: (conversationId) => {
        set((state) => ({
          availableConversations: state.availableConversations.filter(
            conv => conv.id !== conversationId
          )
        }));
      },

      // Initialize with current conversation history
      initializeFromHistory: (conversations) => {
        // Separate current conversation from history
        const currentConversation = conversations.find(conv => conv.isCurrent) || conversations[0];
        const historyConversations = conversations.filter(conv => !conv.isCurrent);

        set({
          attachedConversations: [],
          availableConversations: historyConversations.map(conv => ({
            id: conv.id,
            title: conv.title || `Conversation ${conv.id.slice(0, 6)}`,
            messages: conv.messages || [],
            createdAt: conv.createdAt,
            preview: this.generatePreview(conv.messages || [])
          }))
        });

        return {
          currentConversation,
          availableConversations: historyConversations
        };
      },

      // Generate preview text for conversation
      generatePreview: (messages) => {
        if (!messages || messages.length === 0) {
          return 'No messages';
        }

        // Get last user message or first AI message
        const lastUserMessage = messages.slice().reverse().find(msg => msg.role === 'user');
        const firstAIMessage = messages.find(msg => msg.role === 'assistant');

        return (
          lastUserMessage?.content?.slice(0, 50) ||
          firstAIMessage?.content?.slice(0, 50) ||
          'Conversation'
        );
      }
    }),
    {
      name: 'context-storage',
      partialize: (state) => ({
        attachedConversations: state.attachedConversations,
        availableConversations: state.availableConversations
      }),
    }
  )
);

// Helper function to get context summary for AI
export const getContextSummary = () => {
  const { attachedConversations } = useContextStore.getState();

  if (attachedConversations.length === 0) {
    return 'No additional context attached.';
  }

  const conversationNames = attachedConversations
    .map(conv => conv.title || 'Untitled conversation')
    .join(', ');

  const totalMessages = attachedConversations.reduce(
    (sum, conv) => sum + (conv.messages?.length || 0),
    0
  );

  return `Attached context: ${conversationNames} (${totalMessages} messages total).`;
};