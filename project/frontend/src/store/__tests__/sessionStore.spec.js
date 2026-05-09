import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useSessionStore } from './sessionStore'

// Mock API modules
vi.mock('./api/chat', () => ({
  createSession: vi.fn(),
  getSession: vi.fn(),
  clearSession: vi.fn(),
  sendMessage: vi.fn(),
  getDashboard: vi.fn(),
  healthCheck: vi.fn(),
  getTaskStatus: vi.fn(),
  getJobStatus: vi.fn(),
  streamUpdates: vi.fn(),
}))

vi.mock('./stores/chatStore', () => ({
  useChatStore: vi.fn(),
}))

vi.mock('./stores/taskStore', () => ({
  useTaskStore: vi.fn(),
}))

describe('Session Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with no session', () => {
    const store = useSessionStore()
    expect(store.sessionId).toBeNull()
    expect(store.connectionStatus).toBeNull()
    expect(store.sseConnected).toBe(false)
  })

  it('should create a session', async () => {
    const mockSessionId = 'test-session-id'
    const createSession = require('./api/chat').createSession
    createSession.mockResolvedValue(mockSessionId)

    const store = useSessionStore()
    const result = await store.initSession()
    
    expect(result).toBe(mockSessionId)
    expect(store.sessionId).toBe(mockSessionId)
  })

  it('should handle session initialization error', async () => {
    const createSession = require('./api/chat').createSession
    createSession.mockRejectedValue(new Error('Failed to create session'))

    const store = useSessionStore()
    const result = await store.initSession()
    
    expect(result).toBeNull()
    expect(store.sseConnected).toBe(false)
  })

  it('should load dashboard', async () => {
    const mockDashboard = { system: { queue_depth: 0 } }
    const getDashboard = require('./api/chat').getDashboard
    getDashboard.mockResolvedValue(mockDashboard)

    const store = useSessionStore()
    store.sessionId = 'test-session-id'
    
    const result = await store.loadDashboard()
    
    expect(result).toEqual(mockDashboard)
    expect(store.connectionStatus).toEqual(mockDashboard.system)
  })

  it('should send user message', async () => {
    const mockResponse = {
      response: 'Test response',
      job_status: null,
    }
    const sendMessage = require('./api/chat').sendMessage
    sendMessage.mockResolvedValue(mockResponse)

    const mockAddMessage = vi.fn()
    const mockAddActivity = vi.fn()
    const mockSetThinking = vi.fn()
    const useChatStore = require('./stores/chatStore').useChatStore
    useChatStore.mockReturnValue({
      addMessage: mockAddMessage,
      addActivity: mockAddActivity,
      setThinking: mockSetThinking,
      reset: vi.fn(),
    })

    const store = useSessionStore()
    store.sessionId = 'test-session-id'
    
    await store.sendUserMessage('Hello')
    
    expect(sendMessage).toHaveBeenCalledWith('test-session-id', 'Hello')
    expect(mockSetThinking).toHaveBeenCalledWith(true)
    expect(mockSetThinking).toHaveBeenCalledWith(false)
    expect(mockAddMessage).toHaveBeenCalledTimes(2)
  })

  it('should handle message error', async () => {
    const sendMessage = require('./api/chat').sendMessage
    sendMessage.mockRejectedValue(new Error('API error'))

    const mockAddMessage = vi.fn()
    const mockAddActivity = vi.fn()
    const mockSetThinking = vi.fn()
    const useChatStore = require('./stores/chatStore').useChatStore
    useChatStore.mockReturnValue({
      addMessage: mockAddMessage,
      addActivity: mockAddActivity,
      setThinking: mockSetThinking,
      reset: vi.fn(),
    })

    const store = useSessionStore()
    store.sessionId = 'test-session-id'
    
    await store.sendUserMessage('Hello')
    
    expect(mockAddMessage).toHaveBeenCalled()
    expect(mockAddActivity).toHaveBeenCalled()
  })

  it('should logout', async () => {
    const store = useSessionStore()
    store.sessionId = 'test-session-id'
    store.connectionStatus = { queue_depth: 0 }
    store.sseConnected = true
    store.pollInterval = 123

    const mockChatStoreReset = vi.fn()
    const useChatStore = require('./stores/chatStore').useChatStore
    useChatStore.mockReturnValue({
      reset: mockChatStoreReset,
    })

    const mockTaskStoreReset = vi.fn()
    const useTaskStore = require('./stores/taskStore').useTaskStore
    useTaskStore.mockReturnValue({
      reset: mockTaskStoreReset,
    })

    const mockClearInterval = vi.fn()
    const originalSetInterval = global.setInterval
    global.clearInterval = mockClearInterval

    store.logout()
    
    expect(mockClearInterval).toHaveBeenCalledWith(123)
    expect(store.sessionId).toBeNull()
    expect(store.connectionStatus).toBeNull()
    expect(store.sseConnected).toBe(false)
    expect(mockChatStoreReset).toHaveBeenCalled()
    expect(mockTaskStoreReset).toHaveBeenCalled()

    global.clearInterval = originalSetInterval
  })
})
