// Electron integration for frontend
export const isElectron = () => {
  return window && window.electronAPI
}

export const getBackendUrl = async () => {
  if (isElectron()) {
    try {
      return await window.electronAPI.getBackendUrl()
    } catch (error) {
      console.error('Failed to get backend URL from Electron:', error)
      return 'http://localhost:8000'
    }
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

export const restartBackend = async () => {
  if (isElectron()) {
    try {
      return await window.electronAPI.restartBackend()
    } catch (error) {
      console.error('Failed to restart backend:', error)
      return false
    }
  }
  return false
}

// Window control functions
export const minimizeWindow = () => {
  if (isElectron()) {
    window.electronAPI.minimizeWindow()
  }
}

export const maximizeWindow = () => {
  if (isElectron()) {
    window.electronAPI.maximizeWindow()
  }
}

export const closeWindow = () => {
  if (isElectron()) {
    window.electronAPI.closeWindow()
  }
}

// Storage functions
export const getLocalData = async (key) => {
  if (isElectron()) {
    try {
      return await window.electronAPI.getLocalData(key)
    } catch (error) {
      console.error('Failed to get local data:', error)
      return null
    }
  }
  return localStorage.getItem(key)
}

export const setLocalData = async (key, value) => {
  if (isElectron()) {
    try {
      await window.electronAPI.setLocalData(key, value)
    } catch (error) {
      console.error('Failed to set local data:', error)
    }
  } else {
    localStorage.setItem(key, JSON.stringify(value))
  }
}

// File dialog functions
export const showOpenDialog = async (options = {}) => {
  if (isElectron()) {
    try {
      return await window.electronAPI.showOpenDialog(options)
    } catch (error) {
      console.error('Failed to show open dialog:', error)
      return null
    }
  }
  return null
}

export const showSaveDialog = async (options = {}) => {
  if (isElectron()) {
    try {
      return await window.electronAPI.showSaveDialog(options)
    } catch (error) {
      console.error('Failed to show save dialog:', error)
      return null
    }
  }
  return null
}

// Initialize Electron integration
export const initElectronIntegration = () => {
  if (isElectron()) {
    // Update API client to use electron backend URL
    import('./api/client').then(({ default: apiClient }) => {
      getBackendUrl().then(url => {
        apiClient.defaults.baseURL = url
        console.log(`Electron: Using backend URL: ${url}`)
      })
    })

    // Set up event listeners
    const handleBackendEvent = (event) => {
      console.log('Backend event:', event)
    }

    const handleWindowMaximized = () => {
      document.body.classList.add('window-maximized')
    }

    const handleWindowUnmaximized = () => {
      document.body.classList.remove('window-maximized')
    }

    window.electronAPI.onBackendEvent(handleBackendEvent)
    window.electronAPI.onWindowMaximized(handleWindowMaximized)
    window.electronAPI.onWindowUnmaximized(handleWindowUnmaximized)

    // Clean up on unmount
    return () => {
      window.electronAPI.removeBackendEventListener()
      window.electronAPI.removeWindowEventListeners()
    }
  }
  return () => {} // No-op cleanup for non-Electron
}