import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 全局错误兜底：运行时错误在页面上可见，避免"白屏"却无提示
app.config.errorHandler = (err, instance, info) => {
  console.error('[平台运行时错误]', info, err)
  const msg = String(err?.message || err)
  let box = document.getElementById('app-error-box')
  if (!box) {
    box = document.createElement('div')
    box.id = 'app-error-box'
    box.style.cssText =
      'position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:99999;' +
      'background:#f56c6c;color:#fff;padding:10px 18px;border-radius:6px;' +
      'font-size:13px;max-width:80%;word-break:break-all;box-shadow:0 2px 10px rgba(0,0,0,.3)'
    document.body.appendChild(box)
  }
  box.textContent = `页面出现错误：${msg}（${info || '未知位置'}）`
  setTimeout(() => box.remove(), 8000)
}

app.mount('#app')
