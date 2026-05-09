import apiClient from './client';

export const uploadFile = async (file, sessionId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  const response = await fetch(`${apiClient.defaults.baseURL}/files/upload`, {
    method: 'POST',
    body: formData,
  });
  return response.json();
};

export const listFiles = async () => {
  const response = await apiClient.get('/files');
  return response;
};

export const readFile = async (filename) => {
  const response = await apiClient.get(`/files/${filename}`);
  return response;
};