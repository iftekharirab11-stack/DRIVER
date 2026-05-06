import React, { memo } from 'react';
import { motion } from 'framer-motion';

const MessageBubble = memo(({ message }) => {
  const isUser = message.role === 'user';
  
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
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
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