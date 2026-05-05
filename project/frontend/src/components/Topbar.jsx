import React from 'react';
import { useAppContext } from '../state/appState';

const Topbar = () => {
  const { toggleSidebar, activities } = useAppContext();

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <button
          onClick={toggleSidebar}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-xl font-semibold text-gray-800">MCP Dashboard</h1>
      </div>
      
      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-500">
          {activities.length} activities
        </span>
      </div>
    </header>
  );
};

export default Topbar;