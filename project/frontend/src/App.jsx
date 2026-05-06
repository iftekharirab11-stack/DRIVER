import React, { useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import { useSessionStore } from './store/sessionStore';
import './styles/index.css';

function App() {
  const { sessionId, initSession } = useSessionStore();

  useEffect(() => {
    if (!sessionId) {
      initSession();
    }
  }, [sessionId, initSession]);

  return (
    <div className="h-screen w-full bg-black overflow-hidden">
      <MainLayout />
    </div>
  );
}

export default App;