<template>
  <div class="material-form">
    <!-- 标题栏：根据模式动态显示 -->
    <div class="form-header">
      <h4>{{ isAddMode ? '新增物料' : '物料详情（可编辑）' }}</h4>
      <button class="back-btn" @click="goBack" :disabled="loading">
        ← 返回物料列表
      </button>
    </div>

    <!-- 权限提示：仅编辑模式显示（新增模式无编辑权限提示） -->
    <div v-if="!isAddMode && !hasPermission('material_edit') && !loading" class="no-permission-tip">
      ⚠️ 您暂无编辑物料的权限，所有字段仅可查看！
    </div>

    <!-- 加载/保存状态提示：区分新增/编辑文案 -->
    <div v-if="loading" class="loading">
      {{ isSaving ? (isAddMode ? '正在提交新增...' : '正在保存修改...') : (isAddMode ? '初始化表单中...' : '加载详情中...') }}
    </div>

    <!-- 可编辑/新增区域 -->
    <div v-else class="form-container">
      <div class="form-grid">
        <!-- 物料ID：仅编辑模式显示 -->
        <div class="form-item" v-if="!isAddMode">
          <label>物料ID：</label>
          <span class="detail-value readonly">{{ material.id || '-' }}</span>
        </div>

        <!-- 物料名称：必输，新增/编辑通用 -->
        <div class="form-item" :style="isAddMode ? {} : { gridColumn: 'span 1' }">
          <label>物料名称：<span class="required">*</span></label>
          <input
            v-model="material.name"
            type="text"
            placeholder="请输入物料名称"
            class="detail-input"
            required
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 物料编码：必输，新增/编辑通用 -->
        <div class="form-item">
          <label>物料编码：<span class="required">*</span></label>
          <input
            v-model="material.code"
            type="text"
            placeholder="请输入物料编码"
            class="detail-input"
            required
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 物料分类：新增/编辑通用 -->
        <div class="form-item">
          <label>物料分类：</label>
          <input
            v-model="material.category"
            type="text"
            placeholder="请输入物料分类（如：电子/机械）"
            class="detail-input"
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 单位：新增/编辑通用 -->
        <div class="form-item">
          <label>单位：</label>
          <input
            v-model="material.unit"
            type="text"
            placeholder="请输入单位（如：个/件/米）"
            class="detail-input"
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 供应商：新增/编辑通用 -->
        <div class="form-item">
          <label>供应商：</label>
          <input
            v-model="material.supplier"
            type="text"
            placeholder="请输入供应商名称"
            class="detail-input"
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 数量：新增/编辑通用 -->
        <div class="form-item">
          <label>数量：</label>
          <input
            v-model.number="material.quantity"
            type="number"
            min="0"
            step="1"
            placeholder="请输入物料数量"
            class="detail-input"
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          />
        </div>

        <!-- 特征描述：跨两列，新增/编辑通用 -->
        <div class="form-item" style="grid-column: span 2;">
          <label>特征描述：</label>
          <textarea
            v-model="material.desc"
            placeholder="请输入物料特征描述"
            rows="2"
            class="detail-input desc-input"
            :readonly="!isAddMode && !hasPermission('material_edit')"
            :style="(!isAddMode && !hasPermission('material_edit')) ? { background: '#f8fafc', cursor: 'not-allowed' } : {}"
          ></textarea>
        </div>

        <!-- 物料附件：新增模式始终显示（有新增权限），编辑模式按原有逻辑 -->
        <div class="form-item" style="grid-column: span 2;" v-if="(isAddMode && hasPermission('material_add')) || (!isAddMode && (hasPermission('material_edit') || materialFiles.length))">
          <label>物料附件：</label>
          <div class="file-manager-container">
            <!-- 文件上传区域：新增模式（有新增权限）/编辑模式（有编辑权限）显示 -->
            <div class="upload-area" v-if="(isAddMode && hasPermission('material_add')) || (!isAddMode && hasPermission('material_edit'))">
              <input
                ref="fileInput"
                type="file"
                @change="handleFileChange"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xls,.xlsx,.zip,.rar,.7z,.mp4,.avi,.mov"
                multiple
                class="file-input"
                :disabled="loading || isSaving"
              />
              <button
                type="button"
                class="upload-btn"
                @click="triggerFileInput"
                :disabled="loading || isSaving"
              >
                📤 上传新附件
              </button>
              <span class="file-tip">支持pdf/doc/docx/jpg/png/xls/xlsx/zip/rar/7z/mp4/avi/mov格式，可多选，单个文件最大1GB</span>

              <!-- 待上传文件列表 -->
              <div v-if="pendingFiles.length" class="pending-file-list">
                <div class="pending-title">待上传文件：</div>
                <div v-for="(file, index) in pendingFiles" :key="index" class="file-item">
                  <div class="file-info">
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">({{ formatFileSize(file.size) }})</span>
                  </div>
                  <button type="button" class="remove-file" @click="removePendingFile(index)" :disabled="loading || isSaving">×</button>
                </div>

                <!-- 大文件提示 -->
                <div v-if="hasLargeFile" class="large-file-tip">
                  ⚠️ 检测到大文件，上传可能需要较长时间，请耐心等待！
                </div>
              </div>
            </div>

            <!-- 已上传文件列表：仅编辑模式显示 -->
            <div v-if="!isAddMode && materialFiles.length" class="uploaded-files">
              <div class="uploaded-title">已上传附件：</div>
              <div v-for="(file, index) in materialFiles" :key="file.id || index" class="file-item uploaded-file-item">
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">({{ formatFileSize(file.size) }})</span>
                  <span class="upload-time">{{ file.upload_time || '-' }}</span>
                </div>
                <div class="file-actions">
                  <button
                    class="download-btn"
                    @click="downloadFile(file)"
                    :disabled="loading"
                  >
                    📥 下载
                  </button>
                  <button
                    class="delete-file-btn"
                    @click="deleteUploadedFile(file.id, index)"
                    v-if="hasPermission('material_edit')"
                    :disabled="loading || isSaving"
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>
            </div>

            <!-- 无附件提示：区分新增/编辑模式 -->
            <div
              v-if="!materialFiles.length && !pendingFiles.length"
              class="no-files-tip"
            >
              {{ isAddMode ? '暂无上传附件（可选）' : '暂无物料附件' }}
            </div>
          </div>
        </div>

        <!-- 创建时间：仅编辑模式显示 -->
        <div class="form-item" v-if="!isAddMode">
          <label>创建时间：</label>
          <span class="detail-value readonly">{{ material.create_time || '-' }}</span>
        </div>
      </div>

      <!-- 按钮区域：区分新增/编辑模式 -->
      <div class="save-btn-container">
        <!-- 新增/保存按钮：新增模式显示「提交新增」，编辑模式显示「保存修改」 -->
        <button
          class="save-btn"
          @click="handleSave"
          v-if="isAddMode ? hasPermission('material_add') : hasPermission('material_edit')"
          :disabled="loading || isSaving"
        >
          {{ isSaving ? (isAddMode ? '提交中...' : '保存中...') : (isAddMode ? '✅ 提交新增' : '💾 保存修改') }}
        </button>

        <!-- 删除按钮：仅编辑模式显示 -->
        <button
          class="delete-btn"
          @click="handleDelete"
          v-if="!isAddMode && hasPermission('material_delete')"
          :disabled="loading || !hasPermission('material_delete')"
        >
          🗑️ 删除记录
        </button>

        <!-- 取消按钮：仅新增模式显示 -->
        <button
          class="cancel-btn"
          @click="goBack"
          v-if="isAddMode"
          :disabled="loading || isSaving"
        >
          🚫 取消新增
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeMount, onErrorCaptured } from 'vue';
import request from '@/utils/request';
import { useRouter, useRoute } from 'vue-router';

// 捕获组件错误
onErrorCaptured((error, instance, info) => {
  console.error('物料组件错误：', error, '位置：', info);
  alert('页面加载失败：' + error.message);
  return true;
});

// 核心变量定义
const userPermissions = ref([]);
const permissionLoading = ref(false);
const emptyMsg = ref('');
const router = useRouter();
const route = useRoute();

// 关键：判断是否为新增模式（路由无id参数）
const isAddMode = computed(() => !route.params.id && !route.query.id);

// 物料数据（新增模式初始化空值）
const material = ref({
  id: '',
  name: '',
  code: '',
  category: '',
  unit: '',
  supplier: '',
  quantity: 0,
  desc: '',
  create_time: ''
});

// 文件管理相关
const fileInput = ref(null);
const pendingFiles = ref([]);
const materialFiles = ref([]);
const fileFormData = ref(new FormData());

const loading = ref(false);
const isSaving = ref(false);
const isFileUploading = ref(false);

// 计算属性：检测是否有大文件（大于100MB）
const hasLargeFile = computed(() => {
  return pendingFiles.value.some(file => file.size > 100 * 1024 * 1024);
});

// 格式化文件大小显示
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 初始化权限
const initPermissions = async () => {
  permissionLoading.value = true;
  try {
    const res = await request.get('/get-user-permissions/', {
      withCredentials: true,
      timeout: 5000
    });
    if (res?.code === 200) {
      userPermissions.value = res.data || [];
      localStorage.setItem('user_permissions', JSON.stringify(userPermissions.value));
    } else {
      userPermissions.value = JSON.parse(localStorage.getItem('user_permissions') || '[]');
    }
  } catch (err) {
    userPermissions.value = JSON.parse(localStorage.getItem('user_permissions') || '[]');
    if (err.response?.status === 401) {
      emptyMsg.value = '登录状态失效，请重新登录！';
      setTimeout(() => router.push('/login'), 2000);
    }
  } finally {
    permissionLoading.value = false;
  }
};

// 权限判断核心函数：新增模式适配material_add权限
const hasPermission = (permission) => {
  // 1. 管理员特殊处理
  const userRole = localStorage.getItem('erp_user_role_code') || '';
  if (userRole.toLowerCase() === 'admin') {
    return true;
  }

  // 2. 权限加载中：默认返回false
  if (permissionLoading.value) {
    return false;
  }

  // 3. 新增模式：material_edit 权限替换为 material_add
  if (isAddMode.value && permission === 'material_edit') {
    return userPermissions.value.includes('material_add');
  }

  // 4. 普通用户：校验权限列表
  return userPermissions.value.includes(permission);
};

// 校验物料ID合法性（仅编辑模式用）
const validateMaterialId = (id) => {
  const numId = Number(id);
  const isValid = !isNaN(numId) && numId > 0;
  return isValid;
};

// 初始化页面（区分新增/编辑）
const initPage = () => {
  // 新增模式：无需ID校验
  if (isAddMode.value) return true;

  const materialId = String(route.params.id || route.query.id || '').trim();
  if (!materialId) {
    alert('物料ID为空，无法获取详情！');
    goBack();
    return false;
  }

  if (!validateMaterialId(materialId)) {
    alert(`物料ID格式错误（当前ID：${materialId}），请返回列表页重新选择！`);
    goBack();
    return false;
  }
  return materialId;
};

// 返回列表页
const goBack = () => {
  router.push({ name: 'MaterialTable' }).catch(() => {
    router.push('/layout/basicinfoman/proc-material');
  });
};

// 获取物料附件列表（仅编辑模式用）
const getMaterialFiles = async (materialId) => {
  if (isAddMode.value) return; // 新增模式无附件

  try {
    const res = await request.get(`/get-material-files/${materialId}/`, {
      withCredentials: true,
      timeout: 5000
    });
    if (res?.code === 200) {
      materialFiles.value = res.data || [];
    }
  } catch (err) {
    console.error('获取物料附件失败：', err);
    materialFiles.value = [];
  }
};

// 获取物料详情（仅编辑模式用）
const getMaterialDetail = async () => {
  if (isAddMode.value) return; // 新增模式无需加载详情

  const materialId = initPage();
  if (!materialId) return;

  try {
    loading.value = true;
    const numId = Number(materialId);
    const res = await request.get(`/get-material/${numId}/`, {
      withCredentials: true,
      timeout: 5000
    });

    if (res?.code === 200) {
      material.value = {
        id: res.data.id || '',
        name: res.data.name || '',
        code: res.data.code || '',
        category: res.data.category || '',
        unit: res.data.unit || '',
        supplier: res.data.supplier || '',
        quantity: res.data.quantity || 0,
        desc: res.data.desc || '',
        create_time: res.data.create_time || '-'
      };
      await getMaterialFiles(numId);
    } else {
      alert('获取详情失败：' + (res?.msg || '未知错误'));
    }
  } catch (err) {
    console.error('详情请求失败：', err);
    let errMsg = '获取详情失败，请按以下步骤排查：\n';
    if (err.response) {
      if (err.response.status === 401) {
        errMsg += '1. 登录状态失效 → 请返回登录页重新登录\n';
        setTimeout(() => router.push('/login'), 1500);
      } else if (err.response.status === 404) {
        errMsg += `1. 物料ID${Number(initPage())}不存在 → 请返回列表页选择有效数据\n`;
      } else {
        errMsg += `1. 后端错误 [${err.response.status}]：${err.response.data?.msg || '未知错误'}\n`;
      }
    } else if (err.request) {
      errMsg += '1. 无法连接后端 → 检查8000端口是否启动\n2. 跨域配置 → 检查Django的CORS_ALLOWED_ORIGINS\n';
    } else {
      errMsg += `1. 请求异常：${err.message}\n`;
    }
    alert(errMsg);
  } finally {
    loading.value = false;
  }
};

// 触发文件选择框
const triggerFileInput = () => {
  if (loading.value || isSaving.value) return;
  fileInput.value?.click();
};

// 处理文件选择
const handleFileChange = (e) => {
  if (loading.value || isSaving.value) return;

  const files = e.target.files;
  if (!files || files.length === 0) return;

  const maxSize = 1 * 1024 * 1024 * 1024; // 1GB
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (file.size > maxSize) {
      alert(`⚠️ ${file.name} 超过1GB大小限制，请选择更小的文件`);
      continue;
    }

    if (file.size > 100 * 1024 * 1024) {
      if (!confirm(`⚠️ ${file.name} 大小为${formatFileSize(file.size)}，上传可能需要较长时间，是否继续选择？`)) {
        continue;
      }
    }

    pendingFiles.value.push(file);
    fileFormData.value.append('files', file);
  }

  e.target.value = '';
};

// 移除待上传文件
const removePendingFile = (index) => {
  if (loading.value || isSaving.value) return;

  pendingFiles.value.splice(index, 1);
  fileFormData.value = new FormData();
  pendingFiles.value.forEach(file => {
    fileFormData.value.append('files', file);
  });
};

// 下载已上传文件（仅编辑模式用）
const downloadFile = async (file) => {
  if (loading.value || !file.id || isAddMode.value) return;

  try {
    const materialId = initPage();
    if (!materialId) return;

    const res = await request.get(`/download-material-file/${materialId}/${file.id}/`, {
      responseType: 'blob',
      timeout: 300000,
      withCredentials: true
    });

    const blob = new Blob([res.data]);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();

    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    console.error('文件下载失败：', err);
    let errMsg = '文件下载失败！';
    if (err.response?.status === 404) {
      errMsg += '文件不存在或已被删除';
    } else if (err.response?.status === 401) {
      errMsg += '登录已过期，请重新登录';
      setTimeout(() => router.push('/login'), 1500);
    } else {
      errMsg += err.message || '服务器异常';
    }
    alert(errMsg);
  }
};

// 删除已上传文件（仅编辑模式用）
const deleteUploadedFile = async (fileId, index) => {
  if (loading.value || !fileId || isAddMode.value) return;

  if (!confirm('确定删除该附件吗？删除后不可恢复！')) {
    return;
  }

  try {
    const materialId = initPage();
    if (!materialId) return;

    loading.value = true;
    const res = await request.delete(`/delete-material-file/${materialId}/${fileId}/`, {
      withCredentials: true,
      timeout: 5000
    });

    if (res?.code === 200) {
      alert('附件删除成功！');
      materialFiles.value.splice(index, 1);
    } else {
      alert(`删除失败：${res?.msg || '未知错误'}`);
    }
  } catch (err) {
    console.error('删除附件失败：', err);
    alert('删除附件失败：' + (err.message || '服务器异常'));
  } finally {
    loading.value = false;
  }
};

// 上传待提交的文件（新增/编辑通用）
const uploadPendingFiles = async (materialId) => {
  if (pendingFiles.value.length === 0 || !materialId) return true;

  try {
    isFileUploading.value = true;
    const requestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
        timeout: 300000
      },
      withCredentials: true,
      onUploadProgress: (progressEvent) => {
        if (hasLargeFile.value) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`文件上传进度：${percent}%`);
        }
      }
    };

    const res = await request.post(
      `/upload-material-files/${materialId}/`,
      fileFormData.value,
      requestConfig
    );

    if (res?.code === 200) {
      return true;
    } else {
      alert(`文件上传失败：${res?.msg || '未知错误'}`);
      return false;
    }
  } catch (err) {
    console.error('文件上传失败：', err);
    let errMsg = '文件上传失败！';
    if (err.response?.status === 413) {
      errMsg += '文件大小超过服务器限制';
    } else if (err.message.includes('timeout')) {
      errMsg += '上传超时，请检查网络或文件大小';
    } else {
      errMsg += err.message || '服务器异常';
    }
    alert(errMsg);
    return false;
  } finally {
    isFileUploading.value = false;
  }
};

// 保存/新增物料（核心：区分新增/编辑接口）
const handleSave = async () => {
  // 通用参数校验
  if (!material.value.name?.trim()) {
    alert('⚠️ 物料名称不能为空！');
    return;
  }
  if (!material.value.code?.trim()) {
    alert('⚠️ 物料编码不能为空！');
    return;
  }
  if (material.value.quantity < 0) {
    alert('⚠️ 物料数量不能为负数！');
    material.value.quantity = 0;
    return;
  }

  // 提交数据格式化
  const submitData = {
    name: material.value.name.trim(),
    code: material.value.code.trim(),
    category: material.value.category || '',
    unit: material.value.unit || '',
    supplier: material.value.supplier || '',
    quantity: Number(material.value.quantity) || 0,
    desc: material.value.desc || ''
  };

  try {
    loading.value = true;
    isSaving.value = true;
    let res;

    // 新增模式：调用新增接口
    if (isAddMode.value) {
      res = await request.post(
        '/save-material/',
        submitData,
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 10000, // 延长超时时间
          withCredentials: true
        }
      );
    }
    // 编辑模式：调用更新接口
    else {
      const materialId = initPage();
      if (!materialId) return;
      const numId = Number(materialId);
      res = await request.post(
        `/update-material/${numId}/`,
        material.value,
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 5000,
          withCredentials: true
        }
      );
    }

    if (res?.code === 200) {
      // 新增模式：获取新增后的物料ID
      const newMaterialId = isAddMode.value ? res.data.id : initPage();

      // 上传待提交的文件
      if (pendingFiles.value.length > 0 && newMaterialId) {
        const uploadSuccess = await uploadPendingFiles(newMaterialId);
        if (!uploadSuccess) {
          alert(isAddMode.value ? '物料新增成功，但文件上传失败！' : '物料信息保存成功，但文件上传失败！');
        }
      }

      alert(isAddMode.value ? '✅ 物料新增成功！' : '✅ 保存成功！数据已同步到后台');
      // 清空待上传文件
      pendingFiles.value = [];
      fileFormData.value = new FormData();
      // 刷新物料列表
      if (window.__forceFetchMaterials) {
        window.__forceFetchMaterials();
      }
      // 新增成功后返回列表
      if (isAddMode.value) {
        goBack();
      } else {
        // 编辑模式刷新附件列表
        await getMaterialFiles(newMaterialId);
      }
    } else {
      alert(`❌ ${isAddMode.value ? '新增失败' : '保存失败'}：${res?.msg || '未知错误'}`);
    }
  } catch (err) {
    console.error('💥 提交请求异常：', err);
    let errMsg = '';
    if (err.response) {
      const { status, data } = err.response;
      errMsg = `${isAddMode.value ? '新增失败' : '保存失败'} [${status}]：`;
      if (status === 401) {
        errMsg += '登录状态失效，请重新登录！';
        setTimeout(() => router.push('/login'), 1500);
      } else if (status === 404 && !isAddMode.value) {
        errMsg += `物料ID${Number(initPage())}不存在，无法修改！`;
      } else if (status === 400) {
        errMsg += data?.msg || '参数格式错误，请检查输入！';
      } else {
        errMsg += data?.msg || '后端服务异常，请联系管理员！';
      }
    } else if (err.request) {
      errMsg = `${isAddMode.value ? '新增失败' : '保存失败'}：无法连接到后端服务！\n请检查：\n1. Django服务是否启动（http://127.0.0.1:8000）\n2. 跨域配置是否正确`;
    } else {
      errMsg = `${isAddMode.value ? '新增失败' : '保存失败'}：${err.message}`;
    }
    alert(errMsg);
  } finally {
    isSaving.value = false;
    loading.value = false;
  }
};

// 删除记录（仅编辑模式用）
const handleDelete = async () => {
  if (isAddMode.value) return; // 新增模式无删除功能

  const materialId = initPage();
  if (!materialId) return;

  const numId = Number(materialId);
  if (!confirm(`🗑️ 确定删除ID为${numId}的物料吗？删除后不可恢复！`)) {
    return;
  }

  try {
    loading.value = true;
    const res = await request.delete(`/delete-material/${numId}/`, {
      withCredentials: true,
      timeout: 5000
    });

    if (res?.code === 200) {
      alert(res.msg || '✅ 删除成功！');
      goBack();
    } else {
      alert(`❌ 删除失败：${res?.msg || '未知错误'}`);
    }
  } catch (err) {
    console.error('删除请求失败详情：', err);
    let errMsg = '删除失败，请排查：\n';
    if (err.response?.status === 401) {
      errMsg += '1. 登录状态失效 → 重新登录\n';
      setTimeout(() => router.push('/login'), 1500);
    } else if (err.request) {
      errMsg += '1. 后端未启动（8000端口）\n2. 跨域配置错误\n';
    } else {
      errMsg += err.message;
    }
    alert(errMsg);
  } finally {
    loading.value = false;
  }
};

// 路由就绪后初始化
onBeforeMount(() => {
  console.log('路由参数：', route.params);
});

// 组件挂载：区分新增/编辑模式初始化
onMounted(async () => {
  // 1. 校验登录态
  const isLogin = localStorage.getItem('erp_username');
  if (!isLogin) {
    alert('请先登录！');
    router.push('/login');
    return;
  }

  // 2. 先加载权限
  await initPermissions();

  // 3. 仅编辑模式加载详情，新增模式无需加载
  if (!permissionLoading.value && !isAddMode.value) {
    getMaterialDetail();
  }
});
</script>

<style scoped>
/* 核心样式 */
.material-form {
  margin: 24px auto;
  padding: 24px 32px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  max-width: 1200px;
  width: 95%;
}

/* 必输项星号 */
.required {
  color: #ef4444;
  margin-left: 4px;
}

/* 无权限提示样式 */
.no-permission-tip {
  color: #f59e0b;
  background: #fffbeb;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
  border-left: 4px solid #f59e0b;
}

/* 标题栏 */
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.material-form h4 {
  margin: 0;
  color: #0c4a6e;
  font-size: 18px;
  font-weight: 600;
}

/* 返回按钮 */
.back-btn {
  padding: 8px 16px;
  background: #64748b;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.back-btn:hover {
  background: #475569;
}

.back-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 40px 0;
  color: #64748b;
  font-size: 14px;
}

/* 表单容器 */
.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 表单网格 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px 24px;
  background: white;
  padding: 32px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* 表单项 */
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

/* 只读字段 */
.detail-value.readonly {
  font-size: 14px;
  color: #64748b;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  min-height: 40px;
  box-sizing: border-box;
  display: block;
  background: #f8fafc;
  cursor: not-allowed;
}

/* 输入框 */
.detail-input {
  font-size: 14px;
  color: #334155;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  min-height: 40px;
  box-sizing: border-box;
  width: 100%;
  transition: border-color 0.2s ease;
}

.desc-input {
  min-height: 100px;
  resize: vertical;
  line-height: 1.5;
}

.detail-input:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

/* 文件管理容器样式 */
.file-manager-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

/* 上传区域样式 */
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

/* 已上传文件列表 */
.uploaded-files {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.uploaded-title {
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

.uploaded-file-item {
  border-left-color: #10b981;
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

.upload-time {
  font-size: 11px;
  color: #94a3b8;
}

/* 文件操作按钮 */
.file-actions {
  display: flex;
  gap: 8px;
}

.remove-file, .download-btn, .delete-file-btn {
  padding: 2px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  transition: background 0.2s ease;
}

.remove-file {
  background: #fef2f2;
  color: #ef4444;
}

.remove-file:hover:not(:disabled) {
  background: #fee2e2;
}

.remove-file:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.download-btn {
  background: #ecfdf5;
  color: #10b981;
}

.download-btn:hover:not(:disabled) {
  background: #d1fae5;
}

.download-btn:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.delete-file-btn {
  background: #fef2f2;
  color: #ef4444;
}

.delete-file-btn:hover:not(:disabled) {
  background: #fee2e2;
}

.delete-file-btn:disabled {
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

/* 按钮容器 */
.save-btn-container {
  display: flex;
  justify-content: flex-start;
  padding: 8px 0 0 0;
  gap: 16px;
}

/* 保存/提交按钮 */
.save-btn {
  padding: 12px 24px;
  background: #0ea5e9;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.save-btn:hover:not(:disabled) {
  background: #0284c7;
}

.save-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 删除按钮 */
.delete-btn {
  padding: 12px 24px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.delete-btn:hover:not(:disabled) {
  background: #dc2626;
}

.delete-btn:disabled {
  background: #fca5a5;
  cursor: not-allowed;
}

/* 取消按钮（新增模式） */
.cancel-btn {
  padding: 12px 24px;
  background: #64748b;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.cancel-btn:hover:not(:disabled) {
  background: #475569;
}

.cancel-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 大屏适配 */
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

/* 小屏适配 */
@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
    padding: 20px;
    gap: 12px;
  }

  .form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .back-btn {
    width: 100%;
    padding: 10px;
  }

  .save-btn-container {
    flex-direction: column;
    gap: 8px;
  }

  .save-btn, .delete-btn, .cancel-btn {
    width: 100%;
    padding: 12px;
  }

  .detail-input, .detail-value.readonly {
    padding: 10px;
    font-size: 15px;
    min-height: 44px;
  }

  .material-form {
    max-width: 100%;
    padding: 16px;
    margin: 16px;
    width: calc(100% - 32px);
  }

  /* 移动端文件样式适配 */
  .file-name {
    max-width: 60%;
  }

  .file-actions {
    gap: 4px;
  }

  .download-btn, .delete-file-btn {
    padding: 2px 6px;
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .material-form {
    padding: 16px;
    margin: 8px;
    width: calc(100% - 16px);
  }

  .form-grid {
    gap: 10px;
    padding: 16px;
  }
}
</style>