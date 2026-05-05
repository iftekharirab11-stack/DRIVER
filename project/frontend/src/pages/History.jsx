import React from 'react';
import { useAppContext } from '../state/appState';
import MainLayout from '../layout/MainLayout';

const History = () => {
  const { chatHistory } = useAppContext();

  const mockHistory = chatHistory.length > 0 ? chatHistory : [
    { id: 1, message: 'Show my GitHub repos', response: 'Found 3 repositories', timestamp: '2024-01-15 10:30' },
    { id: 2, message: 'Read latest emails', response: 'Found 5 unread emails', timestamp: '2024-01-15 09:15' },
    { id: 3, message: 'List Drive files', response: 'Found 10 files', timestamp: '2024-01-14 16:45' }
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Chat History</h2>
        
        {mockHistory.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 border border-gray-200 text-center">
            <p className="text-gray-500">No chat history yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {mockHistory.map((chat) => (
              <div key={chat.id} className="bg-white rounded-xl shadow-md p-4 border border-gray-200">
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-500">You:</span>
                  <p className="text-gray-800">{chat.message}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-gray-500">AI:</span>
                  <p className="text-gray-800">{chat.response}</p>
                </div>
                <span className="text-xs text-gray-400 mt-2 block">{chat.timestamp}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default History;