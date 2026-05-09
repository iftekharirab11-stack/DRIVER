import React from 'react';
import Sidebar from '../ui/Sidebar';
import ChatWindow from '../chat/index';
import ChatInput from '../chat/ChatInput';
import ActivityFeed from '../ui/ActivityFeed';
import ConnectedApps from '../views/ConnectedApps';
import Settings from '../views/Settings';
import History from '../views/History';
import { useAppStore } from '../../store/appStore';
import ErrorBoundary from '../system/ErrorBoundary';

const MainLayout = () => {
  const { activeTab } = useAppStore();

  const renderMainContent = () => {
    switch (activeTab) {
      case 'chat':
      case 'new-chat':
        return (
          <ErrorBoundary>
            <div className="flex-1 flex flex-col overflow-hidden">
              <ChatWindow />
              <ChatInput />
            </div>
          </ErrorBoundary>
        );
      case 'apps':
        return (
          <ErrorBoundary>
            <ConnectedApps />
          </ErrorBoundary>
        );
      case 'settings':
        return (
          <ErrorBoundary>
            <Settings />
          </ErrorBoundary>
        );
      case 'history':
        return (
          <ErrorBoundary>
            <History />
          </ErrorBoundary>
        );
      case 'workspaces':
      case 'activity':
      default:
        return (
          <ErrorBoundary>
            <div className="flex-1 flex flex-col overflow-hidden">
              <ChatWindow />
              <ChatInput />
            </div>
          </ErrorBoundary>
        );
    }
  };

  return (
    <div className="flex h-screen w-full bg-black text-white overflow-hidden">
      <ErrorBoundary>
        <Sidebar />
      </ErrorBoundary>

      {renderMainContent()}

      <ErrorBoundary>
        <aside className="w-[300px] h-full border-l border-white/5 bg-black/20 backdrop-blur-xl">
          <ActivityFeed />
        </aside>
      </ErrorBoundary>
    </div>
  );
};

export default MainLayout;