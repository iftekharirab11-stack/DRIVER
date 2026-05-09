import React, { memo, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const MessageBubble = memo(({ message }) => {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;
  const contentRef = useRef(null);

  // Auto-scroll to bottom when content changes (for streaming)
  useEffect(() => {
    if (isStreaming && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [message.content, isStreaming]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`
          max-w-[70%] px-4 py-3 rounded-2xl
          ${isUser
            ? 'bg-indigo-600 text-white rounded-br-md'
            : 'bg-white/5 backdrop-blur-sm border border-white/10 text-gray-100 rounded-bl-md'
          }
        `}
      >
        <div
          ref={contentRef}
          className="text-[15px] leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto"
          style={{ scrollbarWidth: 'thin' }}
        >
          {message.content}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></span>
          )}
        </div>
        {!isUser && (
          <div className="mt-2 text-[10px] text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </motion.div>
  );
});

export default MessageBubble;
