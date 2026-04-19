'use strict'

// Preload 脚本：在渲染进程中运行，contextIsolation=true 保证安全隔离
// 目前不需要向页面暴露任何 Node API，保持最小权限原则

const { contextBridge } = require('electron')

// 仅暴露只读版本信息，供前端展示
contextBridge.exposeInMainWorld('electronBridge', {
  platform: process.platform,
  isElectron: true,
})
