import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AppContext = createContext();

const API_BASE = 'http://localhost:5000';

export const AppProvider = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [connections, setConnections] = useState({
    github: { connected: false, username: null },
    gmail: { connected: false },
    drive: { connected: false }
  });
  const [chatHistory, setChatHistory] = useState([]);
  const [activities, setActivities] = useState([]);
  const [currentPage, setCurrentPage] = useState('/dashboard');

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await axios.get(`${API_BASE}/connections`);
      setConnections(response.data);
    } catch (error) {
      console.error('Failed to fetch connections:', error);
    }
  };

  const addActivity = (message) => {
    const newActivity = {
      id: Date.now(),
      message,
      timestamp: new Date().toLocaleTimeString()
    };
    setActivities(prev => [newActivity, ...prev.slice(0, 49)]);
  };

  const connectApp = async (app) => {
    try {
      const response = await axios.post(`${API_BASE}/${app}/connect`, { code: 'mock_code' });
      addActivity(`Connected to ${app}`);
      
      await fetchConnections();
      
      return response.data;
    } catch (error) {
      console.error('Connection failed:', error);
      throw error;
    }
  };

  const disconnectApp = async (app) => {
    try {
      await axios.post(`${API_BASE}/${app}/disconnect`);
      setConnections(prev => ({
        ...prev,
        [app]: { connected: false, username: null }
      }));
      addActivity(`Disconnected from ${app}`);
    } catch (error) {
      console.error('Disconnection failed:', error);
      throw error;
    }
  };

  const addChat = (message, response) => {
    const chat = {
      id: Date.now(),
      message,
      response,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [chat, ...prev]);
  };

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <AppContext.Provider value={{
      sidebarOpen,
      toggleSidebar,
      closeSidebar,
      connections,
      chatHistory,
      activities,
      currentPage,
      setCurrentPage,
      connectApp,
      disconnectApp,
      addActivity,
      addChat,
      fetchConnections
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};