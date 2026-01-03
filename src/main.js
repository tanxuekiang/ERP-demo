// src/main.js 完整版（包含Element Plus全局注册）
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from './utils/request'; // 导入统一配置的axios实例

// ========== 核心缺失：Element Plus 全局注册 ==========
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 图标库

// 创建应用实例
const app = createApp(App);

// 1. 注册Element Plus组件库
app.use(ElementPlus)

// 2. 全局注册所有Element Plus图标（RoleManager中用到的Search/Plus/Edit/Delete等）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 3. 挂载全局axios
app.config.globalProperties.$axios = axios;

// 4. 挂载路由并启动应用
app.use(router).mount('#app');