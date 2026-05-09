import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import { useSessionStore } from '../../store/sessionStore';
import { useActivityStore, ACTIVITY_TYPES } from '../../store/activityStore';
import { useContextStore } from '../../store/contextStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Paperclip, Send, Attach, FolderPlus } from 'lucide-react';

const ChatInput = () => {
  const [input, setInput] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const { isThinking } = useChatStore();
  const { sessionId, sendUserMessage } = useSessionStore();
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const uploadFile = async (file) => {
    if (!file || !sessionId) return;

    try {
      // Use the new file upload functionality
      await useSessionStore.getState().uploadFile(file);
    } catch (error) {
      console.error('File upload failed:', error);
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.ERROR,
        text: `File upload failed: ${error.message}`
      });
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    try {
      // Use streaming method for better UX
      await useSessionStore.getState().sendUserMessageStream(input.trim());
      setInput('');
    } catch (error) {
      console.error('Message sending failed:', error);
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.ERROR,
        text: `Failed to send message: ${error.message}`
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div 
      className={`px-4 py-4 border-t border-white/5 transition-colors ${dragOver ? 'bg-indigo-600/10' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message or drag files..."
              rows={1}
              className="w-full resize-none px-4 py-3 pr-12 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-600/50 transition-colors"
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 rounded-xl bg-white/5 text-gray-400 hover:bg-white/10 transition-colors"
            title="Upload file"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <button
            type="submit"
            disabled={!input.trim() || isThinking}
            className={`
              p-3 rounded-xl transition-all duration-200
              ${input.trim() && !isThinking
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                : 'bg-white/5 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
      
      {dragOver && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="px-6 py-3 bg-indigo-600 rounded-xl text-white">
            Drop file to upload
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInput;