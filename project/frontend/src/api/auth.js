import apiClient from './client';

export const createSession = async () => {
  const response = await apiClient.post('/session');
  const sessionId = response.session_id;
  localStorage.setItem('session_id', sessionId);
  return sessionId;
};

export const getSession = () => {
  return localStorage.getItem('session_id') || sessionStorage.getItem('session_id');
};

export const clearSession = () => {
  localStorage.removeItem('session_id');
  sessionStorage.removeItem('session_id');
};

export const isAuthenticated = () => {
  return !!getSession();
};