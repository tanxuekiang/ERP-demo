<template>
  <div class="login-page">
    <div class="login-card" :style="{ maxWidth: isRegisterMode ? '480px' : '420px' }">
      <!-- Logo和标题区域 -->
      <div class="logo-container">
        <span class="logo-icon">{{ isRegisterMode ? '👤' : '📊' }}</span>
        <span class="logo-text">{{ isRegisterMode ? '注册ERP账号' : '企业ERP系统' }}</span>
        <!-- 返回登录按钮（仅注册模式显示） -->
        <button v-if="isRegisterMode" class="back-btn" @click="switchMode(false)">
          ← 返回登录
        </button>
      </div>

      <!-- 登录表单 -->
      <form v-if="!isRegisterMode" class="login-form" @submit.prevent="handleLogin">
        <!-- 账号输入框 -->
        <div class="form-item" :class="{ 'form-item-error': tipsText && tipsText.includes('账号') }">
          <label class="form-label">账号</label>
          <input
            v-model="loginForm.username"
            type="text"
            placeholder="请输入账号"
            class="form-input"
            autocomplete="off"
            required
            @input="clearTips"
          />
        </div>

        <!-- 密码输入框 -->
        <div class="form-item" :class="{ 'form-item-error': tipsText && tipsText.includes('密码') }">
          <label class="form-label">密码</label>
          <input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            class="form-input"
            autocomplete="off"
            required
            @input="clearTips"
          />
        </div>

        <div class="form-item">
          <button
            type="submit"
            class="login-btn"
            :disabled="isLoading"
          >
            {{ isLoading ? '登录中...' : '登录系统' }}
          </button>
          <!-- 注册入口按钮 -->
          <button
            type="button"
            class="register-link-btn"
            @click="switchMode(true)"
            :disabled="isLoading"
          >
            还没有账号？立即注册
          </button>
        </div>
      </form>

      <!-- 注册表单 -->
      <form v-if="isRegisterMode" class="login-form" @submit.prevent="handleRegister">
        <!-- 账号输入框 -->
        <div class="form-item" :class="{ 'form-item-error': tipsText && tipsText.includes('账号') }">
          <label class="form-label">注册账号</label>
          <input
            v-model="registerForm.username"
            type="text"
            placeholder="请输入账号（4-20位，字母/数字/下划线）"
            class="form-input"
            autocomplete="off"
            required
            @input="clearTips"
          />
        </div>

        <!-- 密码输入框 -->
        <div class="form-item" :class="{ 'form-item-error': tipsText && tipsText.includes('密码') }">
          <label class="form-label">设置密码</label>
          <input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            class="form-input"
            autocomplete="off"
            required
            @input="clearTips"
          />
        </div>

        <!-- 确认密码 -->
        <div class="form-item" :class="{ 'form-item-error': tipsText && tipsText.includes('确认密码') }">
          <label class="form-label">确认密码</label>
          <input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            class="form-input"
            autocomplete="off"
            required
            @input="clearTips"
          />
        </div>

        <div class="form-item">
          <button
            type="submit"
            class="login-btn"
            :disabled="isLoading"
          >
            {{ isLoading ? '注册中...' : '完成注册' }}
          </button>
        </div>
      </form>

      <!-- 提示信息 -->
      <div
        class="tips"
        v-if="tipsText"
        :class="{
          'tips-error': tipsType === 'error',
          'tips-warning': tipsType === 'warning',
          'tips-success': tipsType === 'success',
          'tips-network': tipsType === 'network'
        }"
      >
        <span class="tips-icon">
          {{
            tipsType === 'error' ? '❌' :
            tipsType === 'warning' ? '⚠️' :
            tipsType === 'success' ? '✅' : '📶'
          }}
        </span>
        {{ tipsText }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()
const isLoading = ref(false)
const tipsText = ref('')
const tipsType = ref('') // error/warning/success/network
const isRegisterMode = ref(false) // 是否为注册模式
let inputTimer = null // 输入防抖定时器

// 登录表单
const loginForm = ref({
  username: 'admin',
  password: '123456'
})

// 注册表单
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

// 页面挂载时重置状态
onMounted(() => {
  clearLoginState()
  isLoading.value = false
  tipsText.value = ''
  tipsType.value = ''
  resetRegisterForm()
})

// 监听表单输入，防抖清除提示
watch([
  () => loginForm.value.username,
  () => loginForm.value.password,
  () => registerForm.value.username,
  () => registerForm.value.password,
  () => registerForm.value.confirmPassword
], () => {
  clearTimeout(inputTimer)
  inputTimer = setTimeout(() => {
    clearTips()
  }, 300)
})

// 清理登录状态
const clearLoginState = () => {
  localStorage.removeItem('erp_is_login')
  localStorage.removeItem('erp_username')
  localStorage.removeItem('erp_user_id')
  localStorage.removeItem('erp_session_id')
}

// 重置注册表单
const resetRegisterForm = () => {
  registerForm.value = {
    username: '',
    password: '',
    confirmPassword: ''
  }
}

// 清除提示信息
const clearTips = () => {
  tipsText.value = ''
  tipsType.value = ''
}

// 统一提示方法
const showTips = (text, type = 'error') => {
  tipsText.value = text
  tipsType.value = type
  // 根据提示类型设置自动清除时间
  const timeoutMap = {
    error: 3000,
    warning: 4000,
    success: 2000,
    network: 10000
  }
  setTimeout(() => {
    clearTips()
  }, timeoutMap[type] || 3000)
}

// 切换登录/注册模式
const switchMode = (isRegister) => {
  isRegisterMode.value = isRegister
  clearTips()
  if (isRegister) {
    // 切换到注册模式时清空登录表单
    loginForm.value.password = ''
  } else {
    // 切换到登录模式时重置注册表单
    resetRegisterForm()
  }
}

// 登录处理逻辑（保留原有逻辑）
const handleLogin = async () => {
  if (isLoading.value) return;

  const { username, password } = loginForm.value;

  // 空值校验
  if (!username && !password) {
    showTips('账号和密码不能为空，请填写完整', 'warning')
    return
  }
  if (!username) {
    showTips('请输入登录账号', 'warning')
    return
  }
  if (!password) {
    showTips('请输入登录密码', 'warning')
    return
  }

  isLoading.value = true
  clearTips()

  try {
    const res = await request.post('/login/', {
      username: username.trim(),
      password: password.trim()
    }, {
      timeout: 8000,
      withCredentials: true // 携带Cookie（关键）
    });

    console.log('登录响应：', res);

    // 登录成功处理
    if (res && res.code === 200) {
      localStorage.setItem('erp_is_login', 'true');
      localStorage.setItem('erp_username', res.data?.username || username);
      localStorage.setItem('erp_user_id', res.data?.user_id || '1');
      localStorage.setItem('erp_session_id', res.data?.session_id || '');

      showTips('登录成功，正在跳转...', 'success')

      setTimeout(() => {
        window.location.href = '/layout/basicinfoman/proc-material';
      }, 800);
    }
    // 登录失败处理
    else {
      let errorMsg = ''
      if (res?.msg?.includes('密码')) {
        errorMsg = '密码错误，请检查后重新输入（默认密码：123456）'
        tipsType.value = 'error'
      } else if (res?.msg?.includes('账号') || res?.msg?.includes('用户')) {
        errorMsg = '账号不存在，请检查账号是否正确'
        tipsType.value = 'error'
      } else {
        errorMsg = res?.msg || '登录失败（默认账号：admin/123456）'
        tipsType.value = 'warning'
      }
      showTips(errorMsg, tipsType.value)
      isLoading.value = false
    }

  } catch (error) {
    console.error('登录错误详情：', error);
    isLoading.value = false

    // 异常场景处理
    if (error.response) {
      const status = error.response.status
      const errData = error.response.data

      if (status === 401) {
        showTips('账号或密码错误，请重新输入', 'error')
      } else if (status === 404) {
        showTips('登录接口未找到，请检查后端服务配置', 'network')
      } else if (status === 500) {
        showTips('服务器内部错误，请稍后重试', 'network')
      } else {
        showTips(errData?.msg || `登录失败（状态码：${status}）`, 'error')
      }
    } else if (error.request) {
      showTips(`网络连接异常！请检查：
1. 后端服务是否启动（127.0.0.1:8000）
2. 前端代理配置是否正确
3. 网络是否正常`, 'network')
    } else {
      showTips(`登录出错：${error.message}`, 'error')
    }
  }
}

// 注册处理逻辑（新增核心功能）
const handleRegister = async () => {
  if (isLoading.value) return;

  const { username, password, confirmPassword } = registerForm.value;

  // 1. 前端表单校验
  // 空值校验
  if (!username || !password || !confirmPassword) {
    showTips('请填写完整的注册信息', 'warning')
    return
  }

  // 账号格式校验（4-20位，字母/数字/下划线）
  const usernameReg = /^[a-zA-Z0-9_]{4,20}$/
  if (!usernameReg.test(username)) {
    showTips('账号格式错误：仅支持字母、数字、下划线，长度4-20位', 'warning')
    return
  }

  // 密码长度校验
  if (password.length < 6) {
    showTips('密码长度不能少于6位', 'warning')
    return
  }

  // 密码一致性校验
  if (password !== confirmPassword) {
    showTips('两次输入的密码不一致', 'error')
    return
  }

  isLoading.value = true
  clearTips()

  try {
    // 2. 调用后端注册接口
    const res = await request.post('/register/', {
      username: username.trim(),
      password: password.trim()
    }, {
      timeout: 8000,
      withCredentials: true // 携带Cookie（关键）
    });

    console.log('注册响应：', res);

    // 3. 注册成功处理
    if (res && res.code === 200) {
      showTips('注册成功！即将返回登录页面', 'success')

      // 重置表单并切换到登录模式
      setTimeout(() => {
        resetRegisterForm()
        switchMode(false)
        // 自动填充注册的账号到登录框
        loginForm.value.username = username
        loginForm.value.password = ''
      }, 1500);
    }
    // 4. 注册失败处理
    else {
      let errorMsg = res?.msg || '注册失败，请稍后重试'
      showTips(errorMsg, 'error')
    }

  } catch (error) {
    console.error('注册错误详情：', error);
    isLoading.value = false

    // 异常场景处理
    if (error.response) {
      const status = error.response.status
      const errData = error.response.data

      if (status === 400) {
        showTips(errData?.msg || '参数错误，请检查输入', 'error')
      } else if (status === 404) {
        showTips('注册接口未找到，请检查后端服务', 'network')
      } else if (status === 500) {
        showTips('服务器内部错误，请稍后重试', 'network')
      } else {
        showTips(`注册失败（状态码：${status}）`, 'error')
      }
    } else if (error.request) {
      showTips(`网络连接异常！请检查：
1. 后端服务是否启动（127.0.0.1:8000）
2. 注册接口(/register/)是否配置正确
3. 网络是否正常`, 'network')
    } else {
      showTips(`注册出错：${error.message}`, 'error')
    }
  } finally {
    isLoading.value = false
  }
}

// 暴露方法
defineExpose({
  clearLoginState,
  switchMode
})

</script>

<style scoped>
.login-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #81c7fe 0%, #4fc3f7 100%);
  padding: 20px;
  box-sizing: border-box;
  margin: 0;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(129, 199, 254, 0.35);
  padding: 40px 30px;
  box-sizing: border-box;
  position: relative;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  margin-bottom: 36px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #0c4a6e;
  letter-spacing: 0.8px;
}

/* 返回登录按钮样式 */
.back-btn {
  position: absolute;
  left: 30px;
  top: 40px;
  background: transparent;
  border: none;
  color: #4fc3f7;
  cursor: pointer;
  font-size: 14px;
  padding: 5px 10px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(79, 195, 247, 0.1);
  color: #0c4a6e;
}

.login-form {
  width: 100%;
}

.form-item {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

/* 错误状态样式 */
.form-item-error .form-input {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.1);
}

.form-item-error .form-label {
  color: #ef4444;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 15px;
  color: #075985;
  transition: color 0.3s ease;
}

.form-input {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  border: 1px solid #e0f2fe;
  padding: 0 12px;
  font-size: 15px;
  color: #075985;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.form-input:focus {
  border-color: #4fc3f7;
  box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.2);
  outline: none;
}

.login-btn {
  width: 100%;
  height: 46px;
  background: linear-gradient(90deg, #81c7fe 0%, #4fc3f7 100%);
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #075985;
  box-shadow: 0 2px 8px rgba(129, 199, 254, 0.25);
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn:hover {
  background: linear-gradient(90deg, #60bfff 0%, #22b8cf 100%);
  color: #0c4a6e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(129, 199, 254, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 注册链接按钮样式 */
.register-link-btn {
  width: 100%;
  height: 40px;
  background: transparent;
  border: 1px solid #4fc3f7;
  border-radius: 8px;
  font-size: 14px;
  color: #4fc3f7;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.3s ease;
}

.register-link-btn:hover {
  background: rgba(79, 195, 247, 0.1);
  color: #0c4a6e;
}

/* 提示样式增强（新增success类型） */
.tips {
  text-align: center;
  font-size: 14px;
  margin-top: 12px;
  padding: 10px 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: pre-line;
  transition: all 0.3s ease;
}

.tips-icon {
  font-size: 16px;
}

.tips-error {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.tips-warning {
  background: rgba(251, 191, 36, 0.08);
  color: #d97706;
  border: 1px solid rgba(251, 191, 36, 0.2);
}

/* 新增成功提示样式 */
.tips-success {
  background: rgba(34, 197, 94, 0.08);
  color: #16a34a;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.tips-network {
  background: rgba(59, 130, 246, 0.08);
  color: #2563eb;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* 移动端适配 */
@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
  }
  .logo-text {
    font-size: 18px;
  }
  .form-input {
    height: 40px;
  }
  .login-btn {
    height: 42px;
    font-size: 15px;
  }
  .register-link-btn {
    height: 38px;
    font-size: 13px;
  }
  .tips {
    font-size: 13px;
    padding: 8px 12px;
  }
  .back-btn {
    top: 30px;
    left: 20px;
    font-size: 13px;
  }
}
</style>