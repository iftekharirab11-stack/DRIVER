import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './state/appState';
import Dashboard from './pages/Dashboard';
import Connections from './pages/Connections';
import History from './pages/History';

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/connections" element={<Connections />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </Router>
    </AppProvider>
  );
}

export default App;