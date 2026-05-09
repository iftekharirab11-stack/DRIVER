const { app, BrowserWindow, ipcMain, Tray, Menu } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let pythonBackend = null
let tray = null

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    },
    title: 'Driver AI - Desktop',
    icon: path.join(__dirname, 'assets', 'icon.png')
  })

  // Load the Vite dev server in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3001')
    mainWindow.webContents.openDevTools()
  } else {
    // Load the production build
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
  }

  // Window management
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function startPythonBackend() {
  // Start the FastAPI backend
  pythonBackend = spawn('python', ['main.py'], {
    cwd: path.join(__dirname, '../../'),
    stdio: ['ignore', 'pipe', 'pipe']
  })

  pythonBackend.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`)
  })

  pythonBackend.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`)
  })

  pythonBackend.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
  })
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'assets', 'tray-icon.png'))
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
        } else {
          createWindow()
        }
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.quit()
      }
    }
  ])
  tray.setToolTip('Driver AI')
  tray.setContextMenu(contextMenu)
  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show()
    }
  })
}

app.whenReady().then(() => {
  // Start backend first
  startPythonBackend()

  // Create main window
  createWindow()

  // Create system tray
  createTray()

  // Set up IPC handlers
  setupIPCHandlers()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Clean up backend
    if (pythonBackend) {
      pythonBackend.kill()
    }
    app.quit()
  }
})

app.on('before-quit', () => {
  // Clean up backend process
  if (pythonBackend) {
    pythonBackend.kill('SIGINT')
  }
})

function setupIPCHandlers() {
  // Handle backend communication
  ipcMain.handle('get-backend-url', () => {
    return process.env.NODE_ENV === 'development'
      ? 'http://localhost:8000'
      : 'http://localhost:8000'
  })

  // Handle app lifecycle
  ipcMain.handle('restart-backend', () => {
    if (pythonBackend) {
      pythonBackend.kill('SIGINT')
      setTimeout(startPythonBackend, 2000)
    }
    return true
  })

  // Add window control handlers
  ipcMain.handle('minimize-window', () => {
    if (mainWindow) {
      mainWindow.minimize()
    }
  })

  ipcMain.handle('maximize-window', () => {
    if (mainWindow) {
      mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize()
    }
  })

  ipcMain.handle('close-window', () => {
    if (mainWindow) {
      mainWindow.close()
    }
  })

  // Notify renderer about window state changes
  mainWindow.on('maximize', () => {
    mainWindow.webContents.send('window-maximized')
  })

  mainWindow.on('unmaximize', () => {
    mainWindow.webContents.send('window-unmaximized')
  })
}