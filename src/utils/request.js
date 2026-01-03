import axios from 'axios';
import router from '@/router/index.js';

// 只保留一个axios实例（合并正确配置）
const request = axios.create({
  // 方案1：使用代理（推荐，避免跨域）
  baseURL: '/api',
  // 方案2：直接连接后端（需确保后端跨域配置正确）
  // baseURL: 'http://127.0.0.1:8000',

  timeout: 300000, // 延长超时时间到5分钟，适配大文件上传
  withCredentials: true, // 关键：携带Session Cookie（必须开启）
  headers: {} // 清空默认headers，避免干扰FormData请求
});

// 请求拦截器：核心优化FormData处理 + 调试日志
request.interceptors.request.use(
  (config) => {
    // 调试日志：打印请求基本信息
    console.log(`[请求拦截器] ${config.method?.toUpperCase()} ${config.url}`);
    console.log(`[请求拦截器] 请求数据类型：${config.data instanceof FormData ? 'FormData' : 'JSON'}`);

    // 核心：区分FormData和普通JSON请求
    if (config.data instanceof FormData) {
      // FormData请求：完全交给浏览器处理（自动生成boundary）
      delete config.headers['Content-Type']; // 必须删除，否则会导致文件上传失败
      config.headers['Accept'] = 'application/json'; // 明确接收JSON响应
      console.log(`[请求拦截器] FormData文件数量：${Array.from(config.data.entries()).filter(([k]) => k === 'files').length}`);
      return config;
    }

    // 普通JSON请求：确保正确的Content-Type和序列化
    if (config.method && ['post', 'put', 'delete', 'patch'].includes(config.method.toLowerCase())) {
      if (config.data && typeof config.data !== 'string') {
        config.data = JSON.stringify(config.data);
      }
      config.headers['Content-Type'] = 'application/json;charset=UTF-8';
    }

    // GET请求：无需设置Content-Type
    if (config.method?.toLowerCase() === 'get') {
      delete config.headers['Content-Type'];
    }

    return config;
  },
  (error) => {
    console.error('[请求拦截器] 请求配置错误：', error);
    return Promise.reject(error);
  }
);

// 响应拦截器：增强错误处理 + 401登录态失效处理 + 调试日志
request.interceptors.response.use(
  (response) => {
    // 调试日志：打印响应信息
    console.log(`[响应拦截器] 状态码：${response.status}，URL：${response.config.url}`);
    console.log(`[响应拦截器] 响应数据：`, response.data);
    return response.data; // 直接返回后端JSON数据（符合前端业务逻辑）
  },
  (error) => {
    // 详细错误日志：方便定位问题
    console.error('[响应拦截器] 请求失败：', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      responseData: error.response?.data,
      message: error.message
    });

    // 处理401未登录/登录过期
    if (error.response?.status === 401 || error.response?.data?.code === 401) {
      alert('⚠️ 登录已过期，请重新登录');
      // 清空本地存储的登录状态
      localStorage.removeItem('erp_is_login');
      localStorage.removeItem('erp_username');
      localStorage.removeItem('erp_user_role_code');
      localStorage.removeItem('user_permissions');
      // 跳转到登录页（强制刷新）
      router.push('/login').then(() => {
        window.location.reload(); // 确保登录态完全重置
      });
    }

    // 处理404接口不存在
    if (error.response?.status === 404) {
      alert(`⚠️ 接口不存在：${error.config.url}`);
    }

    // 处理500服务器错误
    if (error.response?.status === 500) {
      alert(`⚠️ 服务器内部错误：${error.response.data?.msg || '未知错误'}`);
    }

    // 处理网络错误/超时
    if (!error.response) {
      const errMsg = error.message.includes('timeout')
        ? '⚠️ 请求超时（大文件上传建议检查网络）'
        : '⚠️ 网络错误（无法连接后端服务器）';
      alert(errMsg);
    }

    return Promise.reject(error);
  }
);

export default request;