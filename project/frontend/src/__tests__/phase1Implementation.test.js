import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useChatStore } from '../store/chatStore';
import { useSessionStore } from '../store/sessionStore';
import { useActivityStore } from '../store/activityStore';
import { useMemoryStore } from '../store/memoryStore';
import { SessionService } from '../services/sessionService';
import { getMemoryContext } from '../store/memoryStore';

// Mock the API client
vi.mock('../api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: { baseURL: 'http://localhost:3000' }
  }
}));

// Mock the auth API
vi.mock('../api/auth', () => ({
  createSession: vi.fn().mockResolvedValue('test-session-123'),
  getSession: vi.fn().mockReturnValue('test-session-123'),
  clearSession: vi.fn()
}));

describe('Driver AI Phase 1 Implementation Tests', () => {
  beforeEach(() => {
    // Clear all stores before each test
    useChatStore.getState().reset();
    useSessionStore.getState().reset();
    useActivityStore.getState().reset();
    useMemoryStore.getState().reset();

    // Mock EventSource
    global.EventSource = class {
      constructor(url) {
        this.url = url;
        this.listeners = {};
      }
      addEventListener(type, callback) {
        this.listeners[type] = callback;
      }
      dispatchEvent(event) {
        const handler = this.listeners[event.type];
        if (handler) handler(event);
      }
      close() {}
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Memory System', () => {
    it('should initialize memory store with default values', () => {
      const memoryState = useMemoryStore.getState();
      expect(memoryState.memory).toEqual({
        username: null,
        recentTasks: [],
        projectNames: [],
        previousTopics: [],
        preferences: {},
      });
    });

    it('should save and retrieve memory values', () => {
      const { saveMemory, getMemory } = useMemoryStore.getState();

      saveMemory('username', 'John Doe');
      expect(getMemory('username')).toBe('John Doe');

      saveMemory('preferences', { theme: 'dark' });
      expect(getMemory('preferences')).toEqual({ theme: 'dark' });
    });

    it('should add items to memory arrays', () => {
      const { addToMemoryArray, getMemory } = useMemoryStore.getState();

      addToMemoryArray('recentTasks', 'Implement streaming');
      addToMemoryArray('recentTasks', 'Build activity feed');
      addToMemoryArray('projectNames', 'Driver AI');

      expect(getMemory('recentTasks')).toEqual(['Implement streaming', 'Build activity feed']);
      expect(getMemory('projectNames')).toEqual(['Driver AI']);
    });

    it('should generate memory context summary', () => {
      const { updateMemory } = useMemoryStore.getState();

      updateMemory({
        username: 'Test User',
        recentTasks: ['Task 1', 'Task 2', 'Task 3'],
        projectNames: ['Project A'],
        previousTopics: ['Topic 1', 'Topic 2']
      });

      const context = getMemoryContext();
      expect(context).toContain('Test User');
      expect(context).toContain('Task 1');
      expect(context).toContain('Project A');
      expect(context).toContain('Topic 1');
    });
  });

  describe('Activity Feed System', () => {
    it('should add activities to the feed', () => {
      const { addActivity, activities } = useActivityStore.getState();

      addActivity({ type: 'system', text: 'Test activity' });
      expect(activities.length).toBe(1);
      expect(activities[0].text).toBe('Test activity');
      expect(activities[0].type).toBe('system');
    });

    it('should limit activities to 100 items', () => {
      const { addActivity, activities } = useActivityStore.getState();

      for (let i = 0; i < 105; i++) {
        addActivity({ type: 'system', text: `Activity ${i}` });
      }

      expect(activities.length).toBe(100);
    });

    it('should stream activities', () => {
      const { streamActivity, activities } = useActivityStore.getState();

      streamActivity({ type: 'thinking', text: 'AI is thinking...' });
      expect(activities.length).toBe(1);
      expect(activities[0].type).toBe('thinking');
    });
  });

  describe('Streaming Chat Responses', () => {
    it('should handle streaming message chunks', async () => {
      const { sendMessageStream } = useSessionStore.getState();
      const { addMessage, updateMessage, messages } = useChatStore.getState();

      // Mock the streaming API response
      const mockResponse = {
        response: 'This is a test response that will be streamed in chunks'
      };

      // Mock the API call
      const apiClient = await import('../api/client');
      apiClient.default.post.mockResolvedValue(mockResponse);

      // Mock the streaming callbacks
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      // Call the streaming method
      sendMessageStream('test-session-123', 'Hello', onChunk, onComplete, onError);

      // Wait for the streaming to complete
      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledWith(mockResponse.response);
      });

      // Check that chunks were processed
      expect(onChunk).toHaveBeenCalled();
    });

    it('should update message content incrementally', () => {
      const { addMessage, updateMessage, messages } = useChatStore.getState();

      // Add initial message
      const messageId = Date.now();
      addMessage({
        id: messageId,
        role: 'assistant',
        content: '',
        isStreaming: true
      });

      // Simulate streaming chunks
      updateMessage(messageId, { content: 'Hello' });
      updateMessage(messageId, { content: (prev) => prev + ' world' });
      updateMessage(messageId, { content: (prev) => prev + '!', isStreaming: false });

      const finalMessage = messages.find(m => m.id === messageId);
      expect(finalMessage.content).toBe('Hello world!');
      expect(finalMessage.isStreaming).toBe(false);
    });
  });

  describe('Session Management', () => {
    it('should initialize session successfully', async () => {
      const sessionId = await SessionService.initializeSession();
      expect(sessionId).toBe('test-session-123');

      const sessionState = useSessionStore.getState();
      expect(sessionState.sessionId).toBe('test-session-123');
    });

    it('should restore session state', () => {
      // Add some test data
      const { addMessage } = useChatStore.getState();
      const { saveMemory } = useMemoryStore.getState();

      addMessage({
        id: Date.now(),
        role: 'user',
        content: 'Test message',
        timestamp: new Date()
      });

      saveMemory('username', 'Test User');

      // Restore session
      SessionService.restoreSessionState();

      const chatState = useChatStore.getState();
      const memoryState = useMemoryStore.getState();

      expect(chatState.messages.length).toBe(1);
      expect(memoryState.memory.username).toBe('Test User');
    });

    it('should handle session errors gracefully', () => {
      const error = new Error('Test error');
      const result = SessionService.handleNetworkError(error);

      expect(result.error).toContain('Test error');

      const chatState = useChatStore.getState();
      expect(chatState.messages.some(m => m.content.includes('Network issue'))).toBe(true);
    });
  });

  describe('Integration Tests', () => {
    it('should integrate memory with activity feed', () => {
      const { setUsername } = require('../hooks/useMemoryIntegration').useMemoryIntegration();
      const { activities } = useActivityStore.getState();

      // This would normally be called in a component
      // Just testing that the hook exports the expected functions
      expect(typeof setUsername).toBe('function');
    });

    it('should maintain clean architecture with separate stores', () => {
      // Verify that stores are properly separated
      expect(useChatStore).toBeDefined();
      expect(useSessionStore).toBeDefined();
      expect(useActivityStore).toBeDefined();
      expect(useMemoryStore).toBeDefined();

      // Verify that each store has its own state
      const chatState = useChatStore.getState();
      const sessionState = useSessionStore.getState();
      const activityState = useActivityStore.getState();
      const memoryState = useMemoryStore.getState();

      expect(chatState.messages).toBeDefined();
      expect(sessionState.sessionId).toBeDefined();
      expect(activityState.activities).toBeDefined();
      expect(memoryState.memory).toBeDefined();
    });
  });
});