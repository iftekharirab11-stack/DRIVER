import React from 'react';

const History = () => {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">History</h2>
        <p className="text-gray-400">View your conversation history and past sessions.</p>

        <div className="mt-6 bg-black/20 rounded-lg p-4">
          <div className="text-center py-8 text-gray-500">
            <p>No conversation history found</p>
            <p className="text-sm mt-2">Your recent chats will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default History;