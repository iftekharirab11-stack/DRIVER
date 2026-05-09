import { create } from 'zustand';
import { createSession, getSession, clearSession } from '../api/auth';
import { sendMessage, sendMessageStream, getDashboard, streamUpdates } from '../api/chat';
import { useChatStore } from './chatStore';
import { useTaskStore } from './taskStore';
import { useAppStore } from './appStore';
import { useActivityStore, ACTIVITY_TYPES, createActivity } from './activityStore';
import { useMemoryStore, getMemoryContext } from './memoryStore';
import { useContextStore, getContextSummary } from './contextStore';
import { useWorkspaceStore } from './workspaceStore';
import { FileProcessor } from '../services/fileProcessor';

export const useSessionStore = create((set, get) => ({
  sessionId: getSession(),
  connectionStatus: null,
  sseConnected: false,
  pollInterval: null,
  connectionError: null,

  initSession: async () => {
    const { setSessionError, setLoading } = useAppStore.getState();

    try {
      setLoading(true);
      set({ connectionError: null });
      setSessionError(null);

      // Try to create session, but handle network errors gracefully
      try {
        const sessionId = await createSession();
        set({ sessionId });

        useChatStore.getState().addActivity({ type: 'system', text: 'Session initialized' });

        // Only set up streaming and polling if we have a valid session
        try {
          const unsub = streamUpdates(sessionId, (data) => {
            if (data.system) {
              set({ connectionStatus: data.system, sseConnected: true, connectionError: null });
            }
          });

          set((state) => ({ pollInterval: window.setInterval(() => {
            get().loadDashboard();
          }, 5000) }));

          await get().loadDashboard();
        } catch (streamError) {
          console.warn('Streaming setup failed, continuing without real-time updates:', streamError);
          // Continue without streaming if it fails
        }

        return sessionId;
      } catch (sessionError) {
        console.warn('Session creation failed, continuing in offline mode:', sessionError);
        // Continue without a session - app will work in offline mode
        return null;
      }
    } catch (error) {
      console.error('Session init failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Network error';
      set({
        sseConnected: false,
        connectionError: `Session initialization failed: ${errorMessage}`
      });
      setSessionError(`Session initialization failed: ${errorMessage}`);
      useChatStore.getState().addActivity({
        type: 'error',
        text: `Session init failed: ${errorMessage}`
      });
      return null;
    } finally {
      setLoading(false);
    }
  },

  loadDashboard: async () => {
    try {
      const data = await getDashboard();
      set({
        connectionStatus: data.system || {},
        connectionError: null
      });
      return data;
    } catch (error) {
      console.error('Dashboard error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Dashboard unavailable';
      set({
        connectionError: `Failed to load dashboard: ${errorMessage}`
      });
      useChatStore.getState().addActivity({
        type: 'error',
        text: `Dashboard error: ${errorMessage}`
      });
    }
  },

  sendUserMessage: async (text) => {
    const sessionId = get().sessionId;
    if (!sessionId || !text?.trim()) return;

    useChatStore.getState().addActivity({ type: 'user', text });
    useChatStore.getState().setThinking(true);

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    useChatStore.getState().addMessage(userMessage);

    try {
      const response = await sendMessage(sessionId, text.trim());
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      useChatStore.getState().addMessage(aiMessage);
      useChatStore.getState().addActivity({ type: 'update', text: 'Response received' });

      if (response.job_status) {
        useTaskStore.setState({ activeJobs: response.job_status.active_jobs || {} });
      }
    } catch (error) {
      useChatStore.getState().addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      });
      useChatStore.getState().addActivity({ type: 'error', text: error.message });
    } finally {
      useChatStore.getState().setThinking(false);
    }
  },

  sendUserMessageStream: async (text) => {
    const sessionId = get().sessionId;
    if (!sessionId || !text?.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    useChatStore.getState().addMessage(userMessage);
    useChatStore.getState().addActivity({ type: 'user', text });

    // Add initial AI message with empty content for streaming
    const aiMessageId = Date.now() + 1;
    const initialAiMessage = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    useChatStore.getState().addMessage(initialAiMessage);
    useChatStore.getState().setThinking(true);

    // Add activity for thinking process
    useActivityStore.getState().addActivity(createActivity(ACTIVITY_TYPES.THINKING, 'AI is thinking...'));

    return new Promise((resolve, reject) => {
      sendMessageStream(
        sessionId,
        text.trim(),
        (chunk, isFinal) => {
          // Update the streaming message
          useChatStore.getState().updateMessage(aiMessageId, {
            content: (prevContent) => prevContent + chunk,
            isStreaming: !isFinal
          });

          // Add memory context if this is the first chunk
          if (chunk && !isFinal && useChatStore.getState().messages.length === 2) {
            const memoryContext = getMemoryContext();
            if (memoryContext !== 'No memory context available.') {
              useActivityStore.getState().addActivity(
                createActivity(ACTIVITY_TYPES.MEMORY, memoryContext)
              );
            }
          }
        },
        (fullResponse) => {
          // Finalize the message
          useChatStore.getState().updateMessage(aiMessageId, {
            content: fullResponse,
            isStreaming: false
          });

          // Add completion activity
          useActivityStore.getState().addActivity(
            createActivity(ACTIVITY_TYPES.RESPONSE, 'Response completed')
          );

          // Update memory with current task
          const firstWords = fullResponse.split(' ').slice(0, 5).join(' ');
          useMemoryStore.getState().addToMemoryArray('recentTasks', firstWords);

          resolve(fullResponse);
        },
        (error) => {
          // Handle error
          useChatStore.getState().updateMessage(aiMessageId, {
            content: `Error: ${error.message}`,
            isStreaming: false
          });
          useActivityStore.getState().addActivity(
            createActivity(ACTIVITY_TYPES.ERROR, `Error: ${error.message}`)
          );
          reject(error);
        }
      );
    }).finally(() => {
      useChatStore.getState().setThinking(false);
    });
  },

  logout: () => {
    const { pollInterval } = get();
    if (pollInterval) clearInterval(pollInterval);
    clearSession();
    set({ sessionId: null, connectionStatus: null, sseConnected: false });
    useChatStore.getState().reset();
    useTaskStore.getState().reset();
  },

  uploadFile: async (file) => {
    const sessionId = get().sessionId;
    if (!sessionId) {
      throw new Error('No active session');
    }

    try {
      // Validate file
      FileProcessor.validateFile(file);

      // Add processing activity
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.LOADING,
        text: `📄 Processing ${file.name}...`
      });

      // Process file with intelligence
      const processedFile = await FileProcessor.processFile(file);

      // Add file to current workspace
      useWorkspaceStore.getState().addFileToWorkspace(processedFile);

      // Add file upload message to chat
      const fileMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `📎 File uploaded: **${processedFile.fileName}**\n\n${processedFile.summary}\n\n${processedFile.insights.map(insight => `• ${insight}`).join('\n')}`,
        timestamp: new Date(),
        fileId: processedFile.fileId,
        isFileMessage: true
      };

      useChatStore.getState().addMessage(fileMessage);

      // Add success activity
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.SUCCESS,
        text: `✅ Processed ${processedFile.fileName}`
      });

      // Update memory with file context
      useMemoryStore.getState().addToMemoryArray('recentTasks', `Processed file: ${processedFile.fileName}`);

      return processedFile;
    } catch (error) {
      console.error('File upload error:', error);

      // Add error message
      useChatStore.getState().addMessage({
        id: Date.now(),
        role: 'assistant',
        content: `❌ File upload failed: ${error.message}`,
        timestamp: new Date(),
        isError: true
      });

      // Add error activity
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.ERROR,
        text: `File upload failed: ${error.message}`
      });

      throw error;
    }
  },

  askAboutFile: async (fileId, question) => {
    const sessionId = get().sessionId;
    if (!sessionId) {
      throw new Error('No active session');
    }

    // Get file from workspace
    const currentFiles = useWorkspaceStore.getState().getCurrentFiles();
    const file = currentFiles.find(f => f.fileId === fileId);

    if (!file) {
      throw new Error('File not found in workspace');
    }

    try {
      // Add user question to chat
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: `About ${file.fileName}: ${question}`,
        timestamp: new Date(),
        fileContext: fileId
      };

      useChatStore.getState().addMessage(userMessage);
      useChatStore.getState().setThinking(true);

      // Simulate AI response about the file
      const aiResponse = sessionStore.getState().generateFileResponse(file, question);

      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date(),
        fileContext: fileId
      };

      useChatStore.getState().addMessage(aiMessage);

      // Add activity
      useActivityStore.getState().addActivity({
        type: ACTIVITY_TYPES.UPDATE,
        text: `Answered question about ${file.fileName}`
      });

      return aiResponse;
    } catch (error) {
      console.error('File question error:', error);
      throw error;
    } finally {
      useChatStore.getState().setThinking(false);
    }
  },

  generateFileResponse(file, question) {
    // Generate intelligent response based on file content and question
    const responses = [];

    // Add file context
    responses.push(`**About ${file.fileName}:**`);

    // Answer based on question type
    if (question.toLowerCase().includes('summarize') || question.toLowerCase().includes('summary')) {
      responses.push(file.summary);
    } else if (question.toLowerCase().includes('insights') || question.toLowerCase().includes('key points')) {
      responses.push(`Key insights from ${file.fileName}:`);
      file.insights.forEach((insight, index) => {
        responses.push(`• ${insight}`);
      });
    } else if (question.toLowerCase().includes('content') || question.toLowerCase().includes('text')) {
      responses.push(`File content preview: ${file.content.slice(0, 200)}...`);
    } else {
      // General response
      responses.push(file.summary);
      responses.push('\nAdditional insights:');
      file.insights.forEach((insight, index) => {
        responses.push(`• ${insight}`);
      });
    }

    // Add context information
    if (file.metadata) {
      responses.push(`\nFile details: ${Object.entries(file.metadata)
        .map(([key, value]) => `${key}: ${value}`)
        .join(', ')}`);
    }

    return responses.join('\n');
  }
}));