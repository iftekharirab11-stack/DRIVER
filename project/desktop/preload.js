const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  // Backend communication
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),

  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),

  // Event listeners
  onBackendEvent: (callback) => ipcRenderer.on('backend-event', callback),
  onWindowMaximized: (callback) => ipcRenderer.on('window-maximized', callback),
  onWindowUnmaximized: (callback) => ipcRenderer.on('window-unmaximized', callback),
  removeBackendEventListener: () => ipcRenderer.removeAllListeners('backend-event'),
  removeWindowEventListeners: () => {
    ipcRenderer.removeAllListeners('window-maximized')
    ipcRenderer.removeAllListeners('window-unmaximized')
  },

  // Storage operations
  getLocalData: (key) => ipcRenderer.invoke('get-local-data', key),
  setLocalData: (key, value) => ipcRenderer.invoke('set-local-data', key, value),
  removeLocalData: (key) => ipcRenderer.invoke('remove-local-data', key),

  // File operations
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),

  // App information
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getPlatform: () => process.platform
})