import React, { useRef, useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import MessageBubble from './MessageBubble';
import { motion } from 'framer-motion';

const ChatWindow = () => {
  const { messages, isThinking } = useChatStore();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="w-16 h-16 rounded-full bg-indigo-600/20 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16h5.5a2.5 2.5 0 002.5-2.5v-5A2.5 2.5 0 0014.5 6H9a2.5 2.5 0 00-2.5 2.5v5A2.5 2.5 0 009 16z" />
            </svg>
          </div>
          <h2 className="text-xl font-medium text-gray-300 mb-2">How can I help you?</h2>
          <p className="text-gray-500 max-w-sm">
            Start a conversation with your AI assistant. Ask anything, and I'll help you work through it.
          </p>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      )}
      
      {isThinking && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-3 px-6 py-3 max-w-3xl mx-auto"
        >
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.1 }}
                className="w-2 h-2 bg-indigo-400 rounded-full"
              />
            ))}
          </div>
          <span className="text-sm text-gray-400">Thinking...</span>
        </motion.div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatWindow;