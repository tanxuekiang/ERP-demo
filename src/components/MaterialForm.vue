<template>
  <div class="material-form">
    <div class="form-header">
      <h4>物料信息录入</h4>
      <button class="back-btn" @click="goBackToTable" :disabled="loading">
        ← 返回物料列表
      </button>
    </div>

    <!-- 上传进度条 -->
    <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
      <div class="progress-bar" :style="{ width: `${uploadProgress}%`, backgroundColor: progressColor }"></div>
      <span class="progress-text">{{ uploadProgress }}%</span>
    </div>

    <!-- 全局提示（区分成功/错误） -->
    <div v-if="globalTip.msg" :class="['global-tip', globalTip.type]">
      {{ globalTip.icon }} {{ globalTip.msg }}
      <button class="close-tip" @click="clearGlobalTip">×</button>
    </div>

    <!-- 权限校验提示 -->
    <div v-if="!hasAddPermission" class="permission-tip">
      ⚠️ 您暂无新增物料的权限！
    </div>

    <form @submit.prevent="handleSubmit" class="form-container" v-if="hasAddPermission">
      <div class="form-grid">
        <div class="form-item">
          <label class="required">物料名称：</label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="请输入物料名称"
            required
            :disabled="loading"
            class="form-input"
          />
        </div>
        <div class="form-item">
          <label class="required">物料编码：</label>
          <input
            v-model="formData.code"
            type="text"
            placeholder="请输入物料编码"
            required
            :disabled="loading"
            class="form-input"
          />
        </div>
        <div class="form-item">
          <label>物料分类：</label>
          <input
            v-model="formData.category"
            type="text"
            placeholder="请输入物料分类（如：电子/机械）"
            :disabled="loading"
            class="form-input"
          />
        </div>
        <div class="form-item">
          <label>单位：</label>
          <input
            v-model="formData.unit"
            type="text"
            placeholder="请输入单位（如：个/件/米）"
            :disabled="loading"
            class="form-input"
          />
        </div>
        <div class="form-item">
          <label>供应商：</label>
          <input
            v-model="formData.supplier"
            type="text"
            placeholder="请输入供应商名称"
            :disabled="loading"
            class="form-input"
          />
        </div>
        <div class="form-item">
          <label>数量：</label>
          <input
            v-model="formData.quantity"
            type="number"
            min="0"
            step="1"
            placeholder="请输入物料数量"
            :disabled="loading"
            class="form-input"
          />
        </div>

        <!-- 重构后的文件上传区域（整合详情页的文件管理逻辑） -->
        <div class="form-item upload-item">
          <label>物料附件：</label>
          <div class="file-manager-container">
            <!-- 文件上传区域 -->
            <div class="upload-area">
              <input
                ref="fileInput"
                type="file"
                @change="handleFileChange"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xls,.xlsx,.zip,.rar,.7z,.mp4,.avi,.mov"
                multiple
                class="file-input"
                :disabled="loading"
              />
              <button
                type="button"
                class="upload-btn"
                @click="triggerFileInput"
                :disabled="loading"
              >
                📤 选择文件
              </button>
              <span class="file-tip">支持pdf/doc/docx/jpg/png/xls/xlsx/zip/rar/7z/mp4/avi/mov格式，可多选，单个文件最大1GB</span>

              <!-- 待上传文件列表（复用详情页的文件列表样式） -->
              <div v-if="pendingFiles.length" class="pending-file-list">
                <div class="pending-title">待上传文件：</div>
                <div v-for="(file, index) in pendingFiles" :key="index" class="file-item">
                  <div class="file-info">
                    <span class="file-name" :title="file.name">{{ file.name }}</span>
                    <span class="file-size">({{ formatFileSize(file.size) }})</span>
                  </div>
                  <button
                    type="button"
                    class="remove-file"
                    @click="removePendingFile(index)"
                    :disabled="loading"
                  >
                    ×
                  </button>
                </div>
              </div>

              <!-- 大文件提示 -->
              <div v-if="hasLargeFile" class="large-file-tip">
                ⚠️ 检测到大文件（>100MB），上传可能需要较长时间，请耐心等待，请勿刷新页面！
              </div>

              <!-- 无文件提示 -->
              <div v-if="!pendingFiles.length && !loading" class="no-files-tip">
                暂无待上传文件
              </div>
            </div>
          </div>
        </div>

        <div class="form-item desc-item">
          <label>特征描述：</label>
          <textarea
            v-model="formData.desc"
            placeholder="请输入物料特征描述"
            rows="3"
            :disabled="loading"
            class="form-textarea"
          ></textarea>
        </div>
      </div>

      <div class="form-actions">
        <button
          type="button"
          class="reset-btn"
          @click="resetForm"
          :disabled="loading"
        >
          重置
        </button>
        <button
          type="submit"
          class="submit-btn"
          :disabled="loading || !canSubmit"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? '提交中...' : '提交物料信息' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onErrorCaptured, onUnmounted } from 'vue';
import request from '@/utils/request';
import { useRouter, useRoute } from 'vue-router';

// 捕获组件错误
onErrorCaptured((error, instance, info) => {
  console.error('【物料表单组件全局错误】', error, '位置：', info);
  setGlobalTip('error', `表单加载失败：${error.message.slice(0, 50)}（错误位置：${info}）`);
  return true;
});

const router = useRouter();
const route = useRoute();

// 全局提示（整合成功/错误）
const globalTip = ref({
  msg: '',
  type: 'error', // error/success/warning
  icon: '❌'
});

const setGlobalTip = (type, msg) => {
  const iconMap = {
    error: '❌',
    success: '✅',
    warning: '⚠️'
  };
  globalTip.value = {
    msg,
    type,
    icon: iconMap[type] || 'ℹ️'
  };

  // 自动关闭提示（成功提示3秒，错误提示8秒，警告提示5秒）
  const timeout = type === 'success' ? 3000 : type === 'error' ? 8000 : 5000;
  setTimeout(() => {
    clearGlobalTip();
  }, timeout);
};

const clearGlobalTip = () => {
  globalTip.value = { msg: '', type: 'error', icon: '❌' };
};

// 权限相关
const userPermissions = ref([]);
const permissionLoading = ref(true);

// 表单数据
const formData = ref({
  name: '',
  code: '',
  category: '',
  unit: '',
  supplier: '',
  desc: '',
  quantity: 0
});

// 状态管理
const loading = ref(false);
const uploadProgress = ref(0);
const fileInput = ref(null);
const pendingFiles = ref([]); // 待上传文件列表（替换原fileList）
const fileFormData = ref(null); // 存储文件FormData

// 计算属性
// 检测大文件（100MB以上）
const hasLargeFile = computed(() => {
  return pendingFiles.value.some(file => file.size > 100 * 1024 * 1024);
});

// 权限判断
const hasAddPermission = computed(() => {
  const userRole = localStorage.getItem('erp_user_role_code') || '';
  if (userRole.toLowerCase() === 'admin') return true;
  return !permissionLoading.value && userPermissions.value.includes('material_add');
});

// 提交按钮禁用判断
const canSubmit = computed(() => {
  const name = formData.value.name?.trim();
  const code = formData.value.code?.trim();
  return !!name && !!code && formData.value.quantity >= 0;
});

// 进度条颜色
const progressColor = computed(() => {
  if (uploadProgress.value < 30) return '#0ea5e9';
  if (uploadProgress.value < 70) return '#38bdf8';
  return '#0284c7';
});

// 初始化权限
const initPermissions = async () => {
console.log('当前用户权限列表：', userPermissions.value);
console.log('是否有新增权限：', hasPermission('material_add'));
console.log('是否为管理员：', localStorage.getItem('erp_user_role_code'));

// 2. 修复管理员权限判断（兼容大小写/空值）
const hasPermission = (permission) => {
  const userRole = (localStorage.getItem('erp_user_role_code') || '').toLowerCase();
  // 兼容 admin/ADMIN/超级管理员 等多种写法
  if (['admin', 'superadmin', '超级管理员'].includes(userRole)) return true;

  // 权限加载中时，新增模式默认显示按钮（避免闪烁/隐藏）
  if (permissionLoading.value && permission === 'material_add' && isAddMode.value) {
    return true;
  }

  return userPermissions.value.includes(permission);
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 触发文件选择
const triggerFileInput = () => {
  if (loading.value) return;
  if (fileInput.value) {
    fileInput.value.click();
  }
};

// 处理文件选择（复用详情页的文件处理逻辑）
const handleFileChange = (e) => {
  if (loading.value) return;
  const files = Array.from(e.target.files || []);

  // 空文件选择提示
  if (!files.length) {
    setGlobalTip('warning', '未选择任何文件，请重新选择！');
    return;
  }

  // 清空原有列表
  pendingFiles.value = [];
  fileFormData.value = new FormData();
  const errorFiles = [];

  // 逐个校验文件
  for (const file of files) {
    const maxSize = 1 * 1024 * 1024 * 1024; // 1GB

    // 大小超限校验
    if (file.size > maxSize) {
      errorFiles.push(`${file.name}（超过1GB大小限制）`);
      continue;
    }

    // 空文件校验
    if (file.size === 0) {
      errorFiles.push(`${file.name}（空文件）`);
      continue;
    }

    // 大文件确认
    if (file.size > 100 * 1024 * 1024) {
      if (!confirm(`⚠️ 文件【${file.name}】大小为${formatFileSize(file.size)}，上传可能需要较长时间，是否继续选择？`)) {
        errorFiles.push(`${file.name}（用户取消选择）`);
        continue;
      }
    }

    pendingFiles.value.push(file);
    fileFormData.value.append('files', file); // 添加到FormData
  }

  // 清空input值
  e.target.value = '';

  // 选择结果提示
  if (errorFiles.length > 0 && pendingFiles.value.length === 0) {
    setGlobalTip('error', `选择的文件全部无效：${errorFiles.join('、').slice(0, 80)}`);
  } else if (errorFiles.length > 0) {
    setGlobalTip('warning', `部分文件无效已跳过：${errorFiles.join('、').slice(0, 80)}，成功选择${pendingFiles.value.length}个文件！`);
  } else if (pendingFiles.value.length > 0) {
    setGlobalTip('success', `成功选择${pendingFiles.value.length}个文件，可点击提交！`);
  }
};

// 移除待上传文件
const removePendingFile = (index) => {
  if (loading.value) return;
  if (index >= 0 && index < pendingFiles.value.length) {
    const removedFile = pendingFiles.value[index];
    // 移除列表项
    pendingFiles.value.splice(index, 1);
    // 重新构建FormData
    fileFormData.value = new FormData();
    pendingFiles.value.forEach(file => {
      fileFormData.value.append('files', file);
    });
    setGlobalTip('success', `已移除文件【${removedFile.name.slice(0, 20)}】`);
  }
};

// 重置表单
const resetForm = () => {
  if (confirm('确定要重置表单吗？所有已填写内容将被清空！')) {
    formData.value = {
      name: '',
      code: '',
      category: '',
      unit: '',
      supplier: '',
      desc: '',
      quantity: 0
    };
    pendingFiles.value = [];
    fileFormData.value = null;
    clearGlobalTip();
    setGlobalTip('success', '表单已重置！');
  }
};

// 返回列表
const goBackToTable = () => {
  try {
    router.push({
      name: 'MaterialTable',
      path: '/layout/basicinfoman/proc-material'
    }).catch(() => {
      router.push('/layout/basicinfoman/proc-material');
    });
  } catch (err) {
    console.error('【路由跳转失败】', err);
    setGlobalTip('error', '返回列表失败，即将强制跳转！');
    setTimeout(() => {
      window.location.href = '/layout/basicinfoman/proc-material';
    }, 1500);
  }
};

// 上传文件（复用详情页的上传逻辑）
const uploadPendingFiles = async (materialId) => {
  if (pendingFiles.value.length === 0 || !materialId) return { success: true };

  // 上传配置
  const uploadConfig = {
    timeout: 300000, // 5分钟超时
    withCredentials: true,
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    },
    // 上传进度回调
    onUploadProgress: (progressEvent) => {
      console.log('【上传进度原始数据】', progressEvent);
      if (progressEvent.total && progressEvent.total > 0) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        uploadProgress.value = progress;
        console.log(`【上传进度】${progress}%`);
      }
    }
  };

  try {
    const res = await request.post(`/upload-material-files/${materialId}/`, fileFormData.value, uploadConfig);
    if (res.code !== 200) {
      throw new Error(`文件上传失败：${res.msg || '后端返回非200状态码'}`);
    }
    return { success: true };
  } catch (error) {
    console.error('【文件上传失败详情】', error);
    let errMsg = '';
    if (error.response?.status === 413) {
      errMsg = '文件大小超过服务器限制（请检查Django配置：DATA_UPLOAD_MAX_MEMORY_SIZE、FILE_UPLOAD_MAX_MEMORY_SIZE）';
    } else if (error.response?.status === 401) {
      errMsg = '登录状态失效，请重新登录';
      setTimeout(() => router.push('/login'), 2000);
    } else if (error.response?.status === 404) {
      errMsg = `上传接口不存在：/upload-material-files/${materialId}/`;
    } else if (error.message.includes('Network Error')) {
      errMsg = '网络异常，无法连接服务器';
    } else if (error.message.includes('timeout')) {
      errMsg = '上传超时（大文件建议优化网络或分块上传）';
    } else {
      errMsg = error.message || '文件上传失败';
    }
    return { success: false, msg: errMsg };
  }
};

// 提交逻辑
const handleSubmit = async () => {
  clearGlobalTip();

  // 二次权限校验
  const userRole = localStorage.getItem('erp_user_role_code') || '';
  const cachedPerms = JSON.parse(localStorage.getItem('user_permissions') || '[]');
  const realHasAddPermission = userRole.toLowerCase() === 'admin' || cachedPerms.includes('material_add');

  if (!realHasAddPermission) {
    setGlobalTip('error', '您暂无新增物料的权限，无法提交！');
    return;
  }

  // 基础数据校验
  const name = formData.value.name?.trim();
  const code = formData.value.code?.trim();

  if (!name) {
    setGlobalTip('error', '物料名称不能为空，请填写！');
    return;
  }
  if (!code) {
    setGlobalTip('error', '物料编码不能为空，请填写！');
    return;
  }
  if (formData.value.quantity < 0) {
    setGlobalTip('error', '物料数量不能为负数，请修改！');
    return;
  }

  // 大文件确认
  if (hasLargeFile.value && !confirm('⚠️ 当前选择了大文件（>100MB），上传可能需要较长时间，是否确认提交？')) {
    return;
  }

  try {
    loading.value = true;
    uploadProgress.value = 0;

    // 1. 创建物料基础信息
    const materialData = {
      name: name,
      code: code,
      category: formData.value.category?.trim() || '',
      unit: formData.value.unit?.trim() || '',
      supplier: formData.value.supplier?.trim() || '',
      quantity: formData.value.quantity,
      desc: formData.value.desc?.trim() || '',
      creator: localStorage.getItem('erp_username') || ''
    };

    console.log('【提交物料基础信息】', materialData);

    const res = await request.post(
      '/save-material/',
      materialData,
      {
        timeout: 10000,
        withCredentials: true
      }
    );

    if (res.code !== 200) {
      throw new Error(`物料创建失败：${res.msg || '后端未返回错误信息'}`);
    }

    const materialId = res.data?.id;
    if (!materialId) {
      throw new Error('物料创建成功，但未返回物料ID，无法上传附件！');
    }
    console.log('【物料创建成功】ID：', materialId);

    let fileUploadSuccess = true;

    // 2. 上传文件（仅当有文件时执行）
    if (materialId && pendingFiles.value.length > 0) {
      setGlobalTip('warning', '开始上传文件，请耐心等待...');
      const uploadResult = await uploadPendingFiles(materialId);

      if (!uploadResult.success) {
        setGlobalTip('error', `⚠️ 物料【${name}】创建成功，但附件上传失败：${uploadResult.msg}`);
        fileUploadSuccess = false;
      } else {
        uploadProgress.value = 100;
      }
    }

    // 3. 提交成功处理
    if (fileUploadSuccess) {
      setGlobalTip('success', `✅ 物料【${name}】提交成功！即将返回物料列表`);
      // 重置表单
      formData.value = {
        name: '',
        code: '',
        category: '',
        unit: '',
        supplier: '',
        desc: '',
        quantity: 0
      };
      pendingFiles.value = [];
      fileFormData.value = null;

      // 延迟跳转
      setTimeout(() => goBackToTable(), 1500);
    }
  } catch (error) {
    console.error('【提交物料总失败】', error);
    let totalErrMsg = '';

    if (error.response) {
      switch (error.response.status) {
        case 400:
          totalErrMsg = `参数错误：${error.response.data?.msg || '物料编码重复/格式错误'}`;
          break;
        case 401:
          totalErrMsg = '登录已过期，请重新登录！';
          setTimeout(() => router.push('/login'), 1500);
          break;
        case 403:
          totalErrMsg = '您暂无新增物料的权限！';
          break;
        case 404:
          totalErrMsg = `接口不存在：${error.config.url}`;
          break;
        case 500:
          totalErrMsg = `服务器内部错误：${error.response.data?.msg || '后端处理失败'}`;
          break;
        default:
          totalErrMsg = `请求失败（状态码${error.response.status}）：${error.response.data?.msg || '未知错误'}`;
      }
    } else if (error.message.includes('Network Error')) {
      totalErrMsg = '网络异常，无法连接服务器，请检查网络后重试！';
    } else if (error.message.includes('timeout')) {
      totalErrMsg = '请求超时，请检查网络或缩短文件大小后重试！';
    } else {
      totalErrMsg = error.message.slice(0, 80);
    }

    setGlobalTip('error', `❌ 提交失败：${totalErrMsg}`);
  } finally {
    loading.value = false;
    setTimeout(() => {
      uploadProgress.value = 0;
    }, 1000);
  }
};

// 组件卸载时清理
onUnmounted(() => {
  fileFormData.value = null;
  pendingFiles.value = [];
});

// 组件挂载时初始化
onMounted(async () => {
  // 登录状态校验
  const isLogin = localStorage.getItem('erp_username');
  if (!isLogin) {
    setGlobalTip('error', '请先登录系统！');
    router.push('/login');
    return;
  }

  // 初始化权限
  await initPermissions();

  // 表单自动聚焦
  setTimeout(() => {
    const firstInput = document.querySelector('.form-input');
    if (firstInput) firstInput.focus();
  }, 500);
});
</script>

<style scoped>
/* 核心样式 */
.material-form {
  margin: 24px auto;
  padding: 28px 36px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  max-width: 1200px;
  width: 95%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.material-form h4 {
  margin: 0;
  color: #0c4a6e;
  font-size: 20px;
  font-weight: 600;
}

.back-btn {
  padding: 8px 16px;
  background: #64748b;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: #475569;
}

.back-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 全局提示样式 */
.global-tip {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeIn 0.3s ease;
}

.global-tip.error {
  background: #fef2f2;
  border: 1px solid #fecdd3;
  color: #dc2626;
}

.global-tip.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
}

.global-tip.warning {
  background: #fffbeb;
  border: 1px solid #fbbf24;
  color: #92400e;
}

.close-tip {
  padding: 2px 8px;
  background: transparent;
  color: inherit;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: background 0.2s ease;
}

.close-tip:hover {
  background: rgba(0, 0, 0, 0.05);
}

.permission-tip {
  padding: 20px;
  background: #fef2f2;
  border: 1px solid #fecdd3;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
  margin-bottom: 20px;
}

/* 上传进度条 */
.upload-progress {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 16px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: #64748b;
}

/* 表单样式 */
.form-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px 24px;
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item label {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.form-item label.required::after {
  content: '*';
  color: #ef4444;
  margin-left: 4px;
}

.form-input {
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  height: 44px;
  box-sizing: border-box;
  width: 100%;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.form-input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
  opacity: 0.8;
}

.form-textarea {
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  width: 100%;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}

.form-textarea:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.form-textarea:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
  opacity: 0.8;
}

/* 文件管理容器样式（复用详情页样式） */
.file-manager-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-input {
  display: none;
}

.upload-btn {
  padding: 10px 16px;
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
  transition: all 0.2s ease;
  width: fit-content;
}

.upload-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #94a3b8;
}

.upload-btn:disabled {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
}

.file-tip {
  font-size: 12px;
  color: #64748b;
  margin-left: 4px;
}

/* 待上传文件列表 */
.pending-file-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pending-title {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
}

/* 文件项通用样式 */
.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 4px;
  border-left: 3px solid #0ea5e9;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.file-name {
  font-size: 13px;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}

.file-size {
  font-size: 11px;
  color: #64748b;
}

.remove-file {
  padding: 2px 8px;
  background: #fef2f2;
  color: #ef4444;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.remove-file:hover:not(:disabled) {
  background: #fee2e2;
}

.remove-file:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

/* 大文件提示 */
.large-file-tip {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fffbeb;
  border: 1px solid #fbbf24;
  border-radius: 4px;
  font-size: 12px;
  color: #92400e;
}

/* 无文件提示 */
.no-files-tip {
  padding: 12px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  background: #f8fafc;
  border-radius: 4px;
}

/* 描述项 */
.desc-item {
  grid-column: span 2;
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 8px;
}

.reset-btn {
  padding: 10px 20px;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.reset-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #94a3b8;
}

.reset-btn:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.submit-btn {
  padding: 10px 24px;
  background: #0ea5e9;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  background: #0284c7;
}

.submit-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 加载动画 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式适配 */
@media (min-width: 1400px) {
  .material-form {
    max-width: 1400px;
    padding: 32px 40px;
  }
  .form-grid {
    gap: 20px 32px;
    padding: 40px;
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
    padding: 20px;
    gap: 16px;
  }

  .upload-item, .desc-item {
    grid-column: span 1;
  }

  .form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .form-actions {
    flex-direction: column;
    gap: 12px;
  }

  .back-btn, .reset-btn, .submit-btn {
    width: 100%;
    justify-content: center;
  }

  .form-input, .form-textarea {
    padding: 12px;
    font-size: 15px;
    height: 48px;
  }

  .material-form {
    max-width: 100%;
    padding: 16px;
    margin: 16px auto;
    width: calc(100% - 32px);
  }

  .upload-btn {
    width: 100%;
    text-align: center;
  }

  .file-item {
    max-width: 100%;
  }

  .permission-tip {
    padding: 16px;
    font-size: 13px;
  }

  .global-tip {
    font-size: 13px;
    padding: 10px 12px;
  }
}

@media (max-width: 480px) {
  .material-form {
    padding: 16px;
    margin: 8px auto;
    width: calc(100% - 16px);
  }

  .form-grid {
    gap: 12px;
    padding: 16px;
  }

  .form-input, .form-textarea {
    padding: 12px;
    font-size: 15px;
  }
}
</style>