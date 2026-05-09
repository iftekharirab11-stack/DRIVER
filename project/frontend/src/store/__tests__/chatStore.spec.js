import { describe, it, expect, vi } from 'vitest'
import { useChatStore } from '../chatStore'

describe('Chat Store', () => {
  it('should initialize with correct default state', () => {
    const store = useChatStore()
    expect(store.messages).toEqual([])
    expect(store.activities).toEqual([])
    expect(store.isThinking).toBe(false)
  })

  it('should add a message', () => {
    const store = useChatStore()
    const message = {
      id: 1,
      role: 'user',
      content: 'Test message',
      timestamp: new Date(),
    }
    store.addMessage(message)
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0]).toEqual(message)
  })

  it('should reset store', () => {
    const store = useChatStore()
    store.addMessage({ id: 1, role: 'user', content: 'Test', timestamp: new Date() })
    store.addActivity({ type: 'test', text: 'activity' })
    store.setThinking(true)
    
    expect(store.messages).toHaveLength(1)
    expect(store.activities).toHaveLength(1)
    expect(store.isThinking).toBe(true)
    
    store.reset()
    
    expect(store.messages).toEqual([])
    expect(store.activities).toEqual([])
    expect(store.isThinking).toBe(false)
  })

  it('should toggle thinking state', () => {
    const store = useChatStore()
    store.setThinking(true)
    expect(store.isThinking).toBe(true)
    store.setThinking(false)
    expect(store.isThinking).toBe(false)
  })

  it('should add activity', () => {
    const store = useChatStore()
    store.addActivity({ type: 'system', text: 'Test activity' })
    expect(store.activities).toHaveLength(1)
    expect(store.activities[0]).toEqual({
      type: 'system',
      text: 'Test activity',
    })
  })
})
