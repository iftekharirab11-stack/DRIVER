import React from 'react';
import { useAppContext } from '../state/appState';
import MainLayout from '../layout/MainLayout';
import ConnectionCard from '../components/ConnectionCard';

const Connections = () => {
  const { connections } = useAppContext();

  const apps = [
    { 
      id: 'github', 
      name: 'GitHub', 
      icon: '🐙',
      connected: connections.github.connected,
      username: connections.github.username
    },
    { 
      id: 'gmail', 
      name: 'Gmail', 
      icon: '📧',
      connected: connections.gmail.connected
    },
    { 
      id: 'drive', 
      name: 'Google Drive', 
      icon: '📂',
      connected: connections.drive.connected
    }
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">MCP Connections</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {apps.map((app) => (
            <ConnectionCard
              key={app.id}
              app={app.id}
              name={app.name}
              icon={app.icon}
              connected={app.connected}
              username={app.username}
            />
          ))}
        </div>
      </div>
    </MainLayout>
  );
};

export default Connections;