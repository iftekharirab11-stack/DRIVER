import { describe, it, expect } from 'vitest'
import MessageBubble from '../MessageBubble'
import { mount } from '@vue/test-utils'

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const message = {
      role: 'user',
      content: 'Hello, world!',
      timestamp: new Date('2024-01-01T00:00:00Z'),
    }

    const wrapper = mount(MessageBubble, {
      props: { message },
    })

    expect(wrapper.text()).toContain('Hello, world!')
    expect(wrapper.classes()).toContain('justify-end')
  })

  it('renders assistant message correctly', () => {
    const message = {
      role: 'assistant',
      content: 'Hi there!',
      timestamp: new Date('2024-01-01T00:00:00Z'),
    }

    const wrapper = mount(MessageBubble, {
      props: { message },
    })

    expect(wrapper.text()).toContain('Hi there!')
    expect(wrapper.classes()).toContain('justify-start')
  })

  it('displays timestamp for assistant messages', () => {
    const message = {
      role: 'assistant',
      content: 'Test',
      timestamp: new Date('2024-01-01T12:00:00Z'),
    }

    const wrapper = mount(MessageBubble, {
      props: { message },
    })

    const timeElement = wrapper.find('div.text-gray-400')
    expect(timeElement.exists()).toBe(true)
  })

  it('does not display timestamp for user messages', () => {
    const message = {
      role: 'user',
      content: 'Test',
      timestamp: new Date('2024-01-01T12:00:00Z'),
    }

    const wrapper = mount(MessageBubble, {
      props: { message },
    })

    const timeElements = wrapper.findAll('div.text-gray-400')
    // User messages don't have the timestamp div
    expect(timeElements.length).toBe(0)
  })

  it('handles multi-line content with whitespace preservation', () => {
    const message = {
      role: 'assistant',
      content: 'Line 1\nLine 2\n  Line 3 with spaces',
      timestamp: new Date(),
    }

    const wrapper = mount(MessageBubble, {
      props: { message },
    })

    expect(wrapper.text()).toContain('Line 1')
    expect(wrapper.text()).toContain('Line 2')
  })
})
