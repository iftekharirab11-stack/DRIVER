import apiClient from './client';

export const sendMessage = async (sessionId, text) => {
  const response = await apiClient.post('/message', { session_id: sessionId, text });
  return response;
};

export const sendMessageStream = async (sessionId, text, onChunk, onComplete, onError) => {
  try {
    const response = await apiClient.post('/message', { session_id: sessionId, text, stream: true });

    // Simulate streaming if backend doesn't support it yet
    if (response.response) {
      // Split response into chunks for streaming effect
      const fullResponse = response.response;
      const chunks = fullResponse.match(/.{1,50}/g) || [fullResponse]; // Split into ~50 char chunks

      for (let i = 0; i < chunks.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 50)); // Simulate network delay
        onChunk(chunks[i], i === chunks.length - 1);
      }

      onComplete(fullResponse);
    }
  } catch (error) {
    onError(error);
  }
};

export const getDashboard = async () => {
  const response = await apiClient.get('/dashboard');
  return response;
};

export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response;
};

export const getTaskStatus = async (taskId) => {
  const response = await apiClient.get(`/tasks/${taskId}`);
  return response;
};

export const getJobStatus = async (sessionId, jobName) => {
  const response = await apiClient.post('/jobs/status', { session_id: sessionId, job_name: jobName });
  return response;
};

export const streamUpdates = (sessionId, onMessage) => {
  // Use the API client's base URL or fallback to relative path
  const baseUrl = apiClient.defaults.baseURL || '';
  const streamUrl = `${baseUrl}/stream/${sessionId}`.replace('//', '/');

  const eventSource = new EventSource(streamUrl);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Failed to parse SSE data:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    // Auto-reconnect logic
    setTimeout(() => {
      console.log('Attempting to reconnect SSE...');
      streamUpdates(sessionId, onMessage);
    }, 5000);
  };

  return () => {
    eventSource.close();
  };
};
