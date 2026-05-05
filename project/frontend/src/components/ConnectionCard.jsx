import React from 'react';
import { useAppContext } from '../state/appState';

const ConnectionCard = ({ app, name, icon, connected, username }) => {
  const { connectApp, disconnectApp } = useAppContext();

  const handleConnect = async () => {
    try {
      await connectApp(app);
    } catch (error) {
      alert('Connection failed');
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectApp(app);
    } catch (error) {
      alert('Disconnection failed');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{icon}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
            {connected && username && (
              <p className="text-sm text-gray-600">
                Connected to: <a 
                  href={`https://github.com/${username}`} 
                  className="text-blue-600 hover:underline"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  https://github.com/{username}
                </a>
              </p>
            )}
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          connected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {connected ? 'Connected' : 'Not Connected'}
        </div>
      </div>

      <div className="flex space-x-2">
        {connected ? (
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={handleConnect}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Connect
          </button>
        )}
      </div>
    </div>
  );
};

export default ConnectionCard;