'use strict'

const { app, BrowserWindow, dialog, shell, Menu } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')


const FLASK_PORT = parseInt(process.env.FLASK_PORT || '5001', 10)
const IS_DEV = !app.isPackaged

let flaskProcess = null
let mainWindow = null
let loadingWindow = null

// ─── Flask 进程管理 ───────────────────────────────────────────────────────────

function getFlaskBinary() {
  if (IS_DEV) return null
  const ext = process.platform === 'win32' ? '.exe' : ''
  return path.join(process.resourcesPath, `multiversesimulator${ext}`)
}

function pollHealth(port, maxAttempts, interval) {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const timer = setInterval(() => {
      attempts++
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        if (res.statusCode === 200) {
          clearInterval(timer)
          resolve()
        }
      })
      req.on('error', () => {
        if (attempts >= maxAttempts) {
          clearInterval(timer)
          reject(new Error(`后端服务启动超时（已等待 ${(maxAttempts * interval / 1000).toFixed(0)}s）`))
        }
      })
      req.setTimeout(300, () => req.destroy())
    }, interval)
  })
}

async function startFlask() {
  const binary = getFlaskBinary()
  if (!binary) {
    // 开发模式：假设 Flask 已在外部启动
    await pollHealth(FLASK_PORT, 20, 500)
    return
  }

  const userData = app.getPath('userData')
  const env = {
    ...process.env,
    FLASK_PORT: String(FLASK_PORT),
    FLASK_DEBUG: 'false',
    MULTIVERSESIMULATOR_DATA_DIR: userData,
  }

  flaskProcess = spawn(binary, [], {
    env,
    stdio: 'pipe',
    detached: false,
  })

  flaskProcess.stdout.on('data', (d) => console.log('[flask]', d.toString().trimEnd()))
  flaskProcess.stderr.on('data', (d) => console.error('[flask]', d.toString().trimEnd()))

  flaskProcess.on('error', (err) => {
    console.error('[flask] 启动失败:', err)
  })

  // 等待就绪（最多 30 秒）
  await pollHealth(FLASK_PORT, 60, 500)
}

function stopFlask() {
  if (!flaskProcess) return
  try {
    flaskProcess.kill('SIGTERM')
  } catch (e) {
    console.error('[flask] 停止失败:', e)
  }
  flaskProcess = null
}

// ─── 窗口管理 ─────────────────────────────────────────────────────────────────

function createLoadingWindow() {
  loadingWindow = new BrowserWindow({
    width: 340,
    height: 240,
    frame: false,
    resizable: false,
    center: true,
    backgroundColor: '#f5f4ed',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  loadingWindow.loadFile(path.join(__dirname, 'loading.html'))
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 760,
    minWidth: 860,
    minHeight: 600,
    title: '多元宇宙模拟器',
    show: false,
    backgroundColor: '#f5f4ed',
    titleBarStyle: 'hiddenInset',
    // 红绿灯垂直居中于 52px topbar：(52 - 12) / 2 ≈ 20
    trafficLightPosition: { x: 16, y: 20 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
    },
  })

  // 开发模式连 Vite，生产模式连 Flask
  const url = IS_DEV
    ? (process.env.ELECTRON_DEV_URL || `http://localhost:3000`)
    : `http://127.0.0.1:${FLASK_PORT}`

  mainWindow.loadURL(url)

  mainWindow.once('ready-to-show', () => {
    if (loadingWindow && !loadingWindow.isDestroyed()) {
      loadingWindow.close()
      loadingWindow = null
    }
    mainWindow.show()
    if (IS_DEV) mainWindow.webContents.openDevTools({ mode: 'detach' })
  })

  // 外部链接在系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url: href }) => {
    if (href.startsWith('http')) shell.openExternal(href)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => { mainWindow = null })
}

function buildAppMenu() {
  const template = [
    {
      label: app.name,
      submenu: [
        { role: 'about', label: '关于多元宇宙模拟器' },
        { type: 'separator' },
        { role: 'services', label: '服务' },
        { type: 'separator' },
        { role: 'hide', label: '隐藏' },
        { role: 'hideOthers', label: '隐藏其他' },
        { role: 'unhide', label: '显示全部' },
        { type: 'separator' },
        { role: 'quit', label: '退出多元宇宙模拟器' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo', label: '撤销' },
        { role: 'redo', label: '重做' },
        { type: 'separator' },
        { role: 'cut', label: '剪切' },
        { role: 'copy', label: '复制' },
        { role: 'paste', label: '粘贴' },
        { role: 'selectAll', label: '全选' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload', label: '重新加载' },
        { role: 'toggleDevTools', label: '开发者工具' },
        { type: 'separator' },
        { role: 'resetZoom', label: '实际大小' },
        { role: 'zoomIn', label: '放大' },
        { role: 'zoomOut', label: '缩小' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: '全屏' },
      ],
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize', label: '最小化' },
        { role: 'zoom', label: '缩放' },
        { type: 'separator' },
        { role: 'front', label: '前置全部窗口' },
      ],
    },
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

// ─── 应用生命周期 ─────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  buildAppMenu()
  createLoadingWindow()

  try {
    await startFlask()
    createMainWindow()
  } catch (err) {
    if (loadingWindow && !loadingWindow.isDestroyed()) loadingWindow.close()
    dialog.showErrorBox('启动失败', `无法启动后端服务：\n\n${err.message}\n\n请重新启动应用。`)
    app.quit()
  }
})

app.on('window-all-closed', () => {
  // macOS 惯例：关闭所有窗口不退出 app（Dock 仍保留）
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
})

app.on('before-quit', () => stopFlask())

app.on('will-quit', () => stopFlask())
