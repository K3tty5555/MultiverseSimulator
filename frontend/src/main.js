import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

// macOS Electron 环境：给 <html> 加类，用于 CSS 拖拽区域和红绿灯避让
if (window.electronBridge?.platform === 'darwin') {
  document.documentElement.classList.add('macos-app')
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
