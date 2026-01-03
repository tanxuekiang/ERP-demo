<template>
  <div class="erp-role-manager" ref="roleManagerRef">
    <!-- 头部：搜索+操作按钮 -->
    <div class="erp-page-header">
      <div class="erp-page-title">角色权限管理</div>
      <div class="erp-page-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入角色名称/编码搜索"
          class="erp-search-input"
          @keyup.enter="fetchRoles"
          clearable
          size="default"
        >
          <template #prefix><el-icon class="el-icon--left"><Search /></el-icon></template>
        </el-input>
        <el-button
          type="primary"
          icon="Plus"
          @click="openAddDialog"
          class="erp-btn-primary"
          :disabled="dialogLoading"
        >
          新增角色
        </el-button>
        <el-button
          type="danger"
          icon="Delete"
          @click="batchDeleteRoles"
          :disabled="selectedIds.length === 0 || dialogLoading"
          class="erp-btn-danger"
        >
          批量删除选中
        </el-button>
      </div>
    </div>

    <!-- 表格区域 -->
    <el-card class="erp-card-container" shadow="never" border>
      <el-table
        :data="roleList"
        border
        stripe
        v-loading="tableLoading"
        :empty-text="tableLoading ? '加载中...' : '暂无角色数据'"
        @selection-change="handleSelectionChange"
        size="default"
        :header-cell-style="{ background: 'var(--el-fill-color-lighter)', color: 'var(--el-text-color-primary)', fontWeight: 500 }"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="role_name" label="角色名称" min-width="150" />
        <el-table-column prop="role_code" label="角色编码" min-width="120" />
        <el-table-column prop="desc" label="角色描述" min-width="200" />
        <el-table-column label="权限配置" min-width="300">
          <template #default="scope">
            <!-- 增强空值保护 -->
            <el-tag
              v-for="(perm, idx) in (scope.row.permissions || [])"
              :key="idx"
              size="small"
              type="info"
              effect="light"
            >
              {{ getFormLabel(perm.form_name) }}-{{ getActionLabel(perm.action) }}
            </el-tag>
            <span v-if="!(scope.row.permissions && scope.row.permissions.length)" class="erp-text-placeholder">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" align="center">
          <template #default="scope">
            {{ formatTime(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="openEditDialog(scope.row)"
              icon="Edit"
              class="erp-btn-sm"
              :disabled="scope.row.role_code === 'admin' || dialogLoading"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteRole(scope.row.id)"
              icon="Delete"
              class="erp-btn-sm"
              :disabled="scope.row.role_code === 'admin' || dialogLoading"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 + 右下角刷新按钮 -->
      <div class="erp-pagination-container">
        <!-- 刷新按钮 -->
        <el-button
          icon="Refresh"
          type="default"
          size="small"
          @click="fetchRoles"
          :loading="tableLoading"
          class="erp-refresh-btn"
          :disabled="dialogLoading"
        >
          刷新列表
        </el-button>
        <!-- 分页组件 -->
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRoles"
          @current-change="fetchRoles"
          :page-sizes="[10, 20, 50, 100]"
          size="default"
          :disabled="dialogLoading"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="800px"
      @close="handleDialogClose"
      append-to-body
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleBeforeDialogClose"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleRules"
        label-width="100px"
        :disabled="dialogLoading"
        size="default"
        class="erp-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色名称" prop="role_name">
              <el-input
                v-model="roleForm.role_name"
                placeholder="请输入角色名称（如：超级管理员）"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色编码" prop="role_code">
              <el-input
                v-model="roleForm.role_code"
                placeholder="请输入角色编码（如：admin）"
                maxlength="30"
                show-word-limit
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="角色描述" prop="desc">
          <el-input
            v-model="roleForm.desc"
            type="textarea"
            rows="3"
            placeholder="请输入角色描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 权限配置 - 核心修复 -->
        <el-form-item label="权限配置" class="erp-permission-form-item">
          <div class="erp-permission-config">
            <el-card
              v-for="form in formEnums"
              :key="form.value"
              class="erp-permission-card"
              shadow="hover"
              border
            >
              <template #header>
                <span class="erp-card-header-text">{{ form.label }}</span>
              </template>
              <el-checkbox-group
                v-model="roleForm.permission_config[form.value]"
                class="erp-checkbox-group"
                @change="handlePermissionChange"
              >
                <el-checkbox
                  v-for="action in actionEnums"
                  :key="`${form.value}-${action.value}`"
                  :label="action.value"
                  size="default"
                >
                  {{ action.label }}
                </el-checkbox>
              </el-checkbox-group>
            </el-card>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button
          @click="dialogVisible = false"
          class="erp-btn-default"
          :disabled="dialogLoading"
        >
          取消
        </el-button>
        <el-button
          type="primary"
          @click="submitRoleForm"
          :loading="dialogLoading"
          class="erp-btn-primary"
        >
          {{ isEdit ? '保存修改' : '创建角色' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
// 导入所需图标
import { Search, Plus, Edit, Delete, Refresh } from "@element-plus/icons-vue";
import axios from "axios";

// ========== 全局配置 ==========
const request = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json;charset=UTF-8"
  }
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    ElMessage.error("请求异常：" + error.message);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    if (!response.data) {
      ElMessage.error("接口返回数据为空");
      return { data: { code: 500, msg: "接口返回数据异常" } };
    }
    if (response.data.code === 401) {
      ElMessageBox.confirm(
        "登录状态已失效，请重新登录",
        "权限验证",
        {
          confirmButtonText: "去登录",
          cancelButtonText: "取消",
          type: "warning"
        }
      ).then(() => {
        window.location.href = "/login"; // 改为实际登录页路径
      });
    }
    return response;
  },
  (error) => {
    if (error.message.includes("Network Error")) {
      ElMessage.error("网络异常，请检查后端服务是否启动");
    } else if (error.response) {
      ElMessage.error(`接口错误：${error.response.status} - ${error.response.data?.msg || '未知错误'}`);
    } else {
      ElMessage.error("请求失败：" + error.message);
    }
    return Promise.reject(error);
  }
);

// ========== 状态管理 ==========
// 分离loading状态：表格加载/弹窗操作加载
const tableLoading = ref(false);
const dialogLoading = ref(false);
const roleList = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const searchKeyword = ref("");
const selectedIds = ref([]);
// 新增：容器ref，用于滚动到列表顶部
const roleManagerRef = ref(null);

// 弹窗相关
const dialogVisible = ref(false);
const roleFormRef = ref(null);
const isEdit = ref(false);

// 枚举数据（和后端严格对齐）
const formEnums = ref([
  { label: '物料表单', value: 'material' },
  { label: 'ERP用户表单', value: 'erp_user' },
  { label: '角色表单', value: 'role' },
  { label: '订单表单', value: 'order' },
  { label: '产品表单', value: 'product' },
  { label: '合同表单', value: 'contract' }
]);
const actionEnums = ref([
  { label: '查看', value: 'view' },
  { label: '新增', value: 'add' },
  { label: '修改', value: 'edit' },
  { label: '删除', value: 'delete' },
  { label: '导出', value: 'export' }
]);

// ========== 表单配置 ==========
const roleRules = {
  role_name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度为2-50个字符', trigger: 'blur' }
  ],
  role_code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{2,30}$/, message: '编码仅支持字母、数字、下划线，长度2-30位', trigger: 'blur' }
  ],
  desc: [
    { max: 200, message: '角色描述最多200个字符', trigger: 'blur' }
  ]
};

// 核心修复：初始化权限配置对象（确保每个表单都有初始空数组）
const initPermissionConfig = () => {
  const config = {};
  formEnums.value.forEach(form => {
    config[form.value] = [];
  });
  return config;
};

const roleForm = reactive({
  id: "",
  role_name: "",
  role_code: "",
  desc: "",
  permission_config: initPermissionConfig() // 使用初始化函数
});

// ========== 工具函数 ==========
const formatTime = (time) => {
  if (!time) return "-";
  try {
    return new Date(time).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (err) {
    return time;
  }
};

const getFormLabel = (formValue) => {
  const item = formEnums.value.find(item => item.value === formValue);
  return item ? item.label : formValue;
};

const getActionLabel = (actionValue) => {
  const item = actionEnums.value.find(item => item.value === actionValue);
  return item ? item.label : actionValue;
};

// 权限变更处理（调试用）
const handlePermissionChange = (val, formKey) => {
  console.log(`权限变更 - ${formKey}:`, val);
  // 确保权限数组是响应式的
  roleForm.permission_config[formKey] = val;
};

// 安全重置表单（解决重置失败问题）
const resetForm = () => {
  // 先清空表单数据
  Object.assign(roleForm, {
    id: "",
    role_name: "",
    role_code: "",
    desc: "",
    permission_config: initPermissionConfig() // 重新初始化权限配置
  });
  // 延迟重置表单验证状态（nextTick确保DOM更新）
  nextTick(() => {
    if (roleFormRef.value) {
      roleFormRef.value.clearValidate().catch(err => {
        console.warn("表单验证状态重置失败：", err);
      });
    }
  });
};

const handleSelectionChange = (val) => {
  selectedIds.value = val.filter(item => item.role_code !== 'admin').map(item => item.id);
};

// 新增：滚动到列表顶部的方法
const scrollToRoleList = () => {
  if (roleManagerRef.value) {
    roleManagerRef.value.scrollTop = 0;
  }
};

// ========== 弹窗关闭相关处理 ==========
// 弹窗关闭前校验（防止操作中关闭）
const handleBeforeDialogClose = (done) => {
  if (dialogLoading.value) {
    ElMessage.warning("当前有操作正在进行，请等待完成后再关闭");
    return;
  }
  done();
};

// 弹窗关闭后处理
const handleDialogClose = () => {
  // 强制重置loading状态
  dialogLoading.value = false;
  // 重置表单
  resetForm();
};

// ========== 核心业务逻辑 ==========
// 1. 获取角色列表（统一刷新入口）
const fetchRoles = async () => {
  tableLoading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value.trim()
    };
    console.log("请求角色列表参数：", params);
    const res = await request.get("/roles/", { params });

    console.log("角色列表返回数据：", res.data); // 调试用
    if (res.data && res.data.code === 200) {
      const data = res.data.data || {};
      roleList.value = data.list || [];
      total.value = data.total || 0;
      // 仅手动刷新时提示
      if (!dialogVisible.value) {
        ElMessage.success("角色列表已刷新，共加载 " + total.value + " 条数据");
      }
    } else {
      ElMessage.error(res.data?.msg || "获取角色列表失败");
      roleList.value = [];
      total.value = 0;
    }
  } catch (err) {
    console.error("获取角色列表异常：", err);
    ElMessage.error(`获取角色列表失败：${err.message || '网络错误'}`);
    roleList.value = [];
    total.value = 0;
  } finally {
    tableLoading.value = false;
  }
};

// 2. 提交角色表单（新增/修改）- 核心修复
// 2. 提交角色表单（新增/修改）- 核心修复
const submitRoleForm = async () => {
  if (!roleFormRef.value) return;

  try {
    // 表单校验
    const valid = await roleFormRef.value.validate();
    if (!valid) return;

    dialogLoading.value = true;
    let res;
    let successMsg = "";

    // 核心修复：深拷贝确保数据完整性
    const submitData = JSON.parse(JSON.stringify(roleForm));

    // 🔥 关键修复：后端期望接收 permission_config 字段（对象格式），无需转换为 permissions 数组
    // 移除原有的 permissions 转换逻辑，直接保留 permission_config
    // （前端的 permission_config 格式正好匹配后端需求）

    console.log("提交数据：", submitData); // 调试用

    if (isEdit.value) {
      // 编辑角色
      res = await request.put(`/roles/update/${roleForm.id}/`, submitData);
      successMsg = `角色【${roleForm.role_name}】修改成功`;
    } else {
      // 新增角色
      res = await request.post("/roles/add/", submitData);
      successMsg = `角色【${roleForm.role_name}】创建成功`;
    }

    if (res.data.code === 200) {
      ElMessage.success(res.data.msg || successMsg);
      // 第一步：强制关闭弹窗（核心修复）
      dialogVisible.value = false;
      // 第二步：延迟刷新列表（避免DOM未更新）
      nextTick(async () => {
        // 重置页码（新增后回到第一页）
        if (!isEdit.value) {
          currentPage.value = 1;
        }
        // 刷新列表
        await fetchRoles();
        // 滚动到列表顶部
        scrollToRoleList();
      });
    } else {
      ElMessage.error(res.data.msg || (isEdit.value ? "编辑角色失败" : "新增角色失败"));
    }
  } catch (err) {
    console.error("提交角色表单异常：", err);
    ElMessage.error(`${isEdit.value ? "编辑" : "新增"}角色失败：${err.response?.data?.msg || err.message}`);
  } finally {
    // 强制重置loading状态（核心修复）
    dialogLoading.value = false;
  }
};

// 3. 删除单个角色
const deleteRole = async (id) => {
  if (!id) return;
  if (dialogLoading.value) {
    ElMessage.warning("当前有操作正在进行，请等待完成后再操作");
    return;
  }

  try {
    const confirm = await ElMessageBox.confirm(
      "确定要删除该角色吗？删除后无法恢复！",
      "危险操作",
      {
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
        type: "warning",
        dangerMode: true
      }
    );

    if (confirm) {
      tableLoading.value = true;
      const res = await request.delete(`/roles/delete/${id}/`);
      if (res.data.code === 200) {
        ElMessage.success(res.data.msg || "角色删除成功");
        // 强制刷新列表
        await fetchRoles();
        // 滚动到列表顶部
        scrollToRoleList();
      } else {
        ElMessage.error(res.data.msg || "删除角色失败");
      }
    }
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error(`删除角色失败：${err.response?.data?.msg || err.message}`);
    }
  } finally {
    tableLoading.value = false;
  }
};

// 4. 批量删除角色
const batchDeleteRoles = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning("请选择要删除的角色");
    return;
  }
  if (dialogLoading.value) {
    ElMessage.warning("当前有操作正在进行，请等待完成后再操作");
    return;
  }

  try {
    const confirm = await ElMessageBox.confirm(
      `确定要删除选中的${selectedIds.value.length}个角色吗？删除后无法恢复！`,
      "批量删除确认",
      {
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
        type: "warning",
        dangerMode: true
      }
    );

    if (confirm) {
      tableLoading.value = true;
      const res = await request.post("/roles/batch_delete/", { ids: selectedIds.value });
      if (res.data.code === 200) {
        ElMessage.success(res.data.msg || `批量删除${selectedIds.value.length}个角色成功`);
        // 强制刷新列表 + 清空选中
        await fetchRoles();
        selectedIds.value = [];
        // 滚动到列表顶部
        scrollToRoleList();
      } else {
        ElMessage.error(res.data.msg || "批量删除失败");
      }
    }
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error(`批量删除失败：${err.response?.data?.msg || err.message}`);
    }
  } finally {
    tableLoading.value = false;
  }
};

// ========== 弹窗操作 ==========
const openAddDialog = () => {
  resetForm();
  isEdit.value = false;
  dialogVisible.value = true;
};

const openEditDialog = (row) => {
  if (dialogLoading.value) {
    ElMessage.warning("当前有操作正在进行，请等待完成后再操作");
    return;
  }
  if (!row || !row.id) {
    ElMessage.warning("角色数据异常，无法编辑");
    return;
  }
  if (row.role_code === 'admin') {
    ElMessage.warning("禁止修改系统管理员角色");
    return;
  }

  resetForm();
  isEdit.value = true;
  // 赋值表单数据
  roleForm.id = row.id;
  roleForm.role_name = row.role_name || "";
  roleForm.role_code = row.role_code || "";
  roleForm.desc = row.desc || "";

  // 核心修复：解析权限配置（兼容各种异常格式）
  const permissions = Array.isArray(row.permissions) ? row.permissions : [];

  // 先初始化权限配置
  roleForm.permission_config = initPermissionConfig();

  // 赋值权限（核心修复：确保每个权限都正确绑定）
  permissions.forEach(perm => {
    if (perm?.form_name && perm?.action && roleForm.permission_config[perm.form_name]) {
      // 确保是数组且不重复
      if (!roleForm.permission_config[perm.form_name].includes(perm.action)) {
        roleForm.permission_config[perm.form_name].push(perm.action);
      }
    }
  });

  console.log("编辑权限配置：", roleForm.permission_config); // 调试用

  dialogVisible.value = true;
};

// ========== 监听权限变化（调试用） ==========
watch(() => roleForm.permission_config, (newVal) => {
  console.log("权限配置变化：", newVal);
}, { deep: true });

// ========== 初始化 ==========
onMounted(() => {
  fetchRoles(); // 页面加载立即获取列表
});
</script>

<style scoped>
/* 保持原有样式不变 */
.erp-role-manager {
  padding: 16px;
  background: var(--el-bg-color-page);
  min-height: calc(100vh - 64px);
  overflow-y: auto; /* 新增：允许容器滚动 */
  scroll-behavior: smooth; /* 新增：平滑滚动 */
}

.erp-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.erp-page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.erp-page-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.erp-search-input {
  width: 300px;
}

.erp-card-container {
  border-radius: var(--el-border-radius-base);
  box-shadow: var(--el-box-shadow-light);
}

/* 新增：分页+刷新按钮容器样式 */
.erp-pagination-container {
  margin-top: 20px;
  text-align: right;
  padding: 10px 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

/* 刷新按钮样式 */
.erp-refresh-btn {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.erp-form {
  padding: 8px 0;
}

.erp-permission-form-item {
  margin-top: 16px;
}

.erp-permission-config {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
}

.erp-permission-card {
  width: calc(50% - 8px);
  min-width: 280px;
  border-radius: var(--el-border-radius-base);
}

.erp-card-header-text {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.erp-checkbox-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 8px 0;
}

.erp-text-placeholder {
  color: var(--el-text-color-placeholder);
}

.erp-btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

/* 核心修复：权限复选框样式优化 */
:deep(.el-checkbox) {
  margin-bottom: 8px;
}

:deep(.el-checkbox__label) {
  padding-left: 8px;
}

@media (max-width: 1200px) {
  .erp-permission-card {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .erp-page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .erp-page-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .erp-search-input {
    width: 100%;
  }

  .erp-pagination-container {
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }
}

:deep(.el-table) {
  --el-table-header-text-color: var(--el-text-color-primary);
  --el-table-row-hover-bg-color: var(--el-fill-color-light);
}

:deep(.el-card__header) {
  padding: 12px 16px;
  background-color: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 12px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
  text-align: right;
}

/* 禁用状态样式优化 */
:deep(.el-button.is-disabled) {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>