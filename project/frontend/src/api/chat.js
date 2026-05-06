import apiClient from './client';

export const sendMessage = async (sessionId, text) => {
  const response = await apiClient.post('/message', { session_id: sessionId, text });
  return response;
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
  const eventSource = new EventSource(`${apiClient.defaults.baseURL}/stream/${sessionId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
  };
  
  return () => eventSource.close();
};