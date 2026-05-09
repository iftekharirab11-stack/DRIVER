import React, { useEffect, useState } from 'react';
import { isElectron, minimizeWindow, maximizeWindow, closeWindow } from '../../electron';

const DesktopLayout = ({ children }) => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    if (isElectron()) {
      const handleMaximize = () => setIsMaximized(true);
      const handleUnmaximize = () => setIsMaximized(false);

      window.electronAPI.onWindowMaximized(handleMaximize);
      window.electronAPI.onWindowUnmaximized(handleUnmaximize);

      return () => {
        window.electronAPI.removeWindowEventListeners();
      };
    }
  }, []);

  if (!isElectron()) {
    return <>{children}</>;
  }

  return (
    <div className="desktop-app">
      <div className="desktop-title-bar" data-tauri-drag-region>
        <div className="title-bar-left">
          <span className="app-title">Driver AI</span>
        </div>
        <div className="title-bar-right">
          <div className="title-bar-controls">
            <button
              onClick={() => minimizeWindow()}
              className="title-bar-button minimize"
              aria-label="Minimize"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M5 6V4H9V6H5Z" fill="currentColor"/>
              </svg>
            </button>
            <button
              onClick={() => maximizeWindow()}
              className="title-bar-button maximize"
              aria-label="Maximize"
            >
              {isMaximized ? (
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M3 3H7V7H3V3Z M2 2V8H8V2H2Z M1 1H9V9H1V1Z" fill="currentColor"/>
                </svg>
              ) : (
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M2 2H8V8H2V2Z" fill="currentColor"/>
                </svg>
              )}
            </button>
            <button
              onClick={() => closeWindow()}
              className="title-bar-button close"
              aria-label="Close"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M7 3L3 7M3 3L7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div className="desktop-content">
        {children}
      </div>
    </div>
  );
};

export default DesktopLayout;