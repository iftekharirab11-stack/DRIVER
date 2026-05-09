import React, { useEffect, useState } from 'react';
import MainLayout from './components/layout/MainLayout';
import DesktopLayout from './components/desktop/DesktopLayout';
import { useSessionStore } from './store/sessionStore';
import { useAppStore } from './store/appStore';
import { isElectron } from './electron';
import './styles/index.css';
import './styles/desktop.css';

function App() {
  const { sessionId, initSession, connectionError } = useSessionStore();
  const { isLoading, sessionError } = useAppStore();
  const [initializationComplete, setInitializationComplete] = useState(false);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        if (!sessionId) {
          await initSession();
        }
        setInitializationComplete(true);
      } catch (error) {
        console.error('App initialization failed:', error);
        setInitializationComplete(true);
      }
    };

    initializeApp();
  }, [sessionId, initSession]);

  const renderContent = () => {
    if (connectionError || sessionError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen w-full bg-black text-white p-4">
          <div className="max-w-md text-center">
            <div className="w-16 h-16 rounded-full bg-red-600/20 flex items-center justify-center mb-4 mx-auto">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-medium mb-2">Connection Error</h2>
            <p className="text-gray-400 mb-4">
              {connectionError || sessionError || 'Failed to connect to the server'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-medium transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      );
    }

    const Content = isElectron() ? DesktopLayout : React.Fragment;
    return (
      <Content>
        <div className="h-screen w-full bg-black overflow-hidden">
          <MainLayout />
        </div>
      </Content>
    );
  };

  if (!initializationComplete) {
    return (
      <div className="flex items-center justify-center h-screen w-full bg-black">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-white text-lg font-medium">Loading Driver AI...</p>
          {isLoading && <p className="text-gray-400 text-sm">Initializing session...</p>}
        </div>
      </div>
    );
  }

  return renderContent();
}

export default App;