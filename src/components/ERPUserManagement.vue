<template>
  <div class="erp-user-management" style="display: block !important; min-height: 500px; width: 100%;">
    <!-- 页面标题与操作区 -->
    <div class="table-header">
      <h4>ERP用户管理</h4>
      <div class="header-actions">
        <!-- 表格内新增：点击后在表格首行显示新增行 -->
        <button class="add-btn" @click="showAddRow" :disabled="loading || addRowVisible">
          ➕ 新增用户
        </button>
        <!-- 批量删除按钮：仅选中行时可用 -->
        <button
          class="delete-btn"
          @click="handleBatchDelete"
          :disabled="loading || selectedIds.length === 0"
        >
          🗑️ 批量删除选中
        </button>
      </div>
    </div>

    <!-- 骨架屏加载状态 -->
    <div v-if="loading || roleLoading" class="skeleton-container">
      <div class="skeleton-row" v-for="i in 8" :key="i">
        <div class="skeleton-col col-checkbox"></div>
        <div class="skeleton-col col-id"></div>
        <div class="skeleton-col col-name"></div>
        <div class="skeleton-col col-role"></div>
        <div class="skeleton-col col-password"></div>
        <div class="skeleton-col col-confirm"></div>
        <div class="skeleton-col col-actions"></div>
      </div>
    </div>

    <!-- 空数据/异常提示 -->
    <div v-else-if="!hasData">
      {{ emptyMsg }}
    </div>

    <!-- 表格 + 分页 -->
    <div v-else>
      <div class="table-wrapper" style="max-height: 500px; overflow: auto;">
        <table class="material-table">
          <thead>
            <tr>
              <!-- 全选复选框列 -->
              <th class="col-checkbox">
                <input
                  type="checkbox"
                  v-model="allChecked"
                  @change="handleAllCheck"
                  :disabled="loading || userList.length === 0"
                  class="check-all"
                >
              </th>
              <th class="col-id">ID</th>
              <th class="col-name">用户名</th>
              <th class="col-role">所属角色</th>
              <th class="col-password">密码</th>
              <th class="col-confirm">确认密码</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <!-- 表格内新增行（含角色选择） -->
            <tr v-if="addRowVisible" class="add-row">
              <td class="col-checkbox">
                <input type="checkbox" disabled class="check-row">
              </td>
              <td class="col-id">-</td>
              <td class="col-name">
                <input
                  v-model="addForm.username"
                  placeholder="请输入用户名（字母/数字/下划线）"
                  class="edit-input"
                  @blur="validateUsername"
                >
                <span v-if="addForm.usernameError" class="error-tip">{{ addForm.usernameError }}</span>
              </td>
              <td class="col-role">
                <select v-model="addForm.role_id" class="edit-select" @change="validateRole">
                  <option value="">请选择角色</option>
                  <option v-for="role in roleList" :key="role.id" :value="role.id">
                    {{ role.role_name }}
                  </option>
                </select>
                <span v-if="addForm.roleError" class="error-tip">{{ addForm.roleError }}</span>
              </td>
              <td class="col-password">
                <input
                  v-model="addForm.password"
                  type="password"
                  placeholder="请输入密码（至少6位）"
                  class="edit-input"
                  show-password
                >
              </td>
              <td class="col-confirm">
                <input
                  v-model="addForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  class="edit-input"
                  show-password
                >
              </td>
              <td class="col-actions">
                <button class="save-btn" @click="saveAddRow" :disabled="!addForm.username || !addForm.password || !addForm.role_id">✅ 保存</button>
                <button class="cancel-btn" @click="hideAddRow">❌ 取消</button>
              </td>
            </tr>

            <!-- 用户列表行（含角色展示/编辑） -->
            <tr v-for="item in userList" :key="item.id" class="table-row">
              <!-- 行复选框 -->
              <td class="col-checkbox">
                <input
                  type="checkbox"
                  :value="item.id"
                  v-model="selectedIds"
                  @change="handleRowCheck"
                  :disabled="loading || item.username === 'admin'"
                  class="check-row"
                >
              </td>
              <td class="col-id">{{ item.id }}</td>
              <td class="col-name">
                <!-- admin用户标记 -->
                <span>{{ item.username }}</span>
                <span v-if="item.username === 'admin'" class="admin-tag">系统管理员</span>
              </td>
              <td class="col-role">
                <!-- 角色编辑状态显示下拉框，否则显示角色名称 -->
                <select
                  v-if="editRoleId === item.id"
                  v-model="editRoleForm.role_id"
                  class="edit-select"
                >
                  <option value="">请选择角色</option>
                  <option v-for="role in roleList" :key="role.id" :value="role.id">
                    {{ role.role_name }}
                  </option>
                </select>
                <span v-else>
                  {{ item.role_name || '未分配角色' }}
                </span>
              </td>
              <td class="col-password">
                <input
                  v-if="editId === item.id"
                  v-model="editForm.password"
                  type="password"
                  placeholder="请输入新密码（至少6位）"
                  class="edit-input"
                  show-password
                >
                <span v-else>●●●●●●</span>
              </td>
              <td class="col-confirm">
                <span v-if="editId === item.id" class="edit-tip">点击保存确认修改</span>
                <span v-else-if="editRoleId === item.id" class="edit-tip">点击保存确认角色修改</span>
                <span v-else>-</span>
              </td>
              <td class="col-actions">
                <!-- 禁止修改/删除admin用户 -->
                <template v-if="item.username !== 'admin'">
                  <!-- 密码修改按钮 -->
                  <button
                    class="edit-btn"
                    @click="toggleEditRow(item.id)"
                    :disabled="loading || (editId !== null && editId !== item.id) || editRoleId === item.id"
                  >
                    {{ editId === item.id ? '取消密码修改' : '修改密码' }}
                  </button>
                  <!-- 角色修改按钮 -->
                  <button
                    class="role-btn"
                    @click="toggleEditRoleRow(item.id)"
                    :disabled="loading || (editRoleId !== null && editRoleId !== item.id) || editId === item.id"
                  >
                    {{ editRoleId === item.id ? '取消角色修改' : '分配角色' }}
                  </button>
                  <!-- 保存按钮（密码/角色通用） -->
                  <button
                    class="save-btn"
                    @click="saveUserInfo(item.id)"
                    :disabled="loading || !(editId === item.id || editRoleId === item.id) || (editId === item.id && !editForm.password)"
                  >
                    保存
                  </button>
                  <!-- 删除按钮 -->
                  <button
                    class="delete-btn"
                    @click="handleSingleDelete(item.id)"
                    :disabled="loading"
                  >
                    删除
                  </button>
                </template>
                <span v-else class="disabled-text">不可操作</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <div class="pagination-info">
          共 {{ totalCount }} 条 | 第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
          <span v-if="selectedIds.length > 0" class="selected-count">
            已选中 {{ selectedIds.length }} 条
          </span>
        </div>
        <div class="pagination-btns">
          <button @click="changePage(1)" :disabled="currentPage === 1 || loading" class="page-btn">首页</button>
          <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1 || loading" class="page-btn">上一页</button>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages || loading" class="page-btn">下一页</button>
          <button @click="changePage(totalPages)" :disabled="currentPage === totalPages || loading" class="page-btn">尾页</button>
          <div class="page-jump">
            <input type="number" v-model.number="jumpPage" min="1" :max="totalPages" placeholder="页码" @keyup.enter="jumpToPage">
            <button @click="jumpToPage" class="jump-btn" :disabled="!jumpPage || jumpPage < 1 || jumpPage > totalPages || loading">跳转</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 刷新按钮 -->
    <button class="refresh-btn" @click="handleRefresh" :disabled="loading || roleLoading" title="刷新用户数据">
      ♻️
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onErrorCaptured, onUnmounted, shallowRef } from 'vue';
import request from '@/utils/request';
import { useRouter, useRoute } from 'vue-router';

// 防抖函数
const debounce = (fn, delay = 300) => {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
};

// 捕获渲染错误
onErrorCaptured((error, instance, info) => {
  console.error('组件错误：', error, '位置：', info);
  emptyMsg.value = '页面加载失败：' + error.message;
  loading.value = false;
  roleLoading.value = false;
  return true;
});

const router = useRouter();
const route = useRoute();

// 基础数据
const userList = shallowRef([]);
const roleList = shallowRef([]); // 角色列表
const loading = ref(false);
const roleLoading = ref(false); // 角色加载状态
const emptyMsg = ref('暂无用户数据，请先录入！');

// 选择相关状态
const allChecked = ref(false);
const selectedIds = ref([]);

// 缓存配置
const cache = ref({ data: [], time: 0, page: 1 });
const roleCache = ref({ data: [], time: 0 }); // 角色缓存
const CACHE_DURATION = 5000;

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const totalCount = ref(0);
const totalPages = ref(0);
const jumpPage = ref(1);

// 表格内新增行状态（含角色）
const addRowVisible = ref(false);
const addForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  role_id: '', // 新增角色ID字段
  usernameError: '',
  roleError: ''
});

// 表格内编辑行状态
const editId = ref(null); // 当前编辑密码的用户ID
const editRoleId = ref(null); // 当前编辑角色的用户ID
const editForm = ref({
  password: '',
  confirmPassword: ''
});
const editRoleForm = ref({
  role_id: '' // 编辑角色ID
});

// 计算属性：判断是否有数据
const hasData = computed(() => {
  return userList.value.length > 0 && !loading.value && !roleLoading.value;
});

// 监听用户列表变化，重置选中/编辑状态
watch([userList, currentPage], () => {
  allChecked.value = false;
  selectedIds.value = [];
  // 重置编辑/新增状态
  addRowVisible.value = false;
  editId.value = null;
  editRoleId.value = null;
  addForm.value = {
    username: '',
    password: '',
    confirmPassword: '',
    role_id: '',
    usernameError: '',
    roleError: ''
  };
  editForm.value = { password: '', confirmPassword: '' };
  editRoleForm.value = { role_id: '' };
}, { immediate: true });

// 全选/取消全选逻辑（排除admin）
const handleAllCheck = () => {
  if (loading.value) return;
  if (allChecked.value) {
    selectedIds.value = userList.value.filter(item => item.username !== 'admin').map(item => item.id);
  } else {
    selectedIds.value = [];
  }
};

// 行复选框变化，更新全选状态
const handleRowCheck = () => {
  const editableUsers = userList.value.filter(item => item.username !== 'admin');
  allChecked.value = editableUsers.length > 0 &&
    selectedIds.value.length === editableUsers.length;
};

// 获取角色列表（带缓存）
const fetchRoles = async (forceRefresh = false) => {
  if (roleLoading.value) return;

  const now = Date.now();
  // 缓存逻辑：5秒内复用
  if (!forceRefresh && roleCache.value.time + CACHE_DURATION > now) {
    roleList.value = roleCache.value.data;
    return;
  }

  roleLoading.value = true;
  try {
 const res = await request.get('/roles/', {
  params: { page: 1, page_size: 100, _t: now },
  timeout: 3000
});
    if (res && res.code === 200) {
      roleList.value = res.data.list || [];
      roleCache.value = {
        data: roleList.value,
        time: now
      };
    } else {
      console.warn('获取角色列表失败：', res.msg);
      roleList.value = [];
    }
  } catch (error) {
    console.error('获取角色列表失败：', error);
    roleList.value = [];
    alert(`获取角色列表失败：${error.message || '网络异常'}`);
  } finally {
    roleLoading.value = false;
  }
};

// 显示新增行（先加载角色）
const showAddRow = async () => {
  await fetchRoles(); // 确保角色列表已加载
  addRowVisible.value = true;
  // 重置新增表单
  addForm.value = {
    username: '',
    password: '',
    confirmPassword: '',
    role_id: '',
    usernameError: '',
    roleError: ''
  };
  // 滚动到表格顶部
  setTimeout(() => {
    const tableWrapper = document.querySelector('.table-wrapper');
    if (tableWrapper) tableWrapper.scrollTop = 0;
  }, 100);
};

// 隐藏新增行
const hideAddRow = () => {
  addRowVisible.value = false;
  addForm.value = {
    username: '',
    password: '',
    confirmPassword: '',
    role_id: '',
    usernameError: '',
    roleError: ''
  };
};

// 验证用户名
const validateUsername = () => {
  const username = addForm.value.username.trim();
  if (!username) {
    addForm.value.usernameError = '用户名不能为空';
    return false;
  }
  if (!/^[a-zA-Z0-9_]{4,20}$/.test(username)) {
    addForm.value.usernameError = '用户名仅支持字母、数字、下划线，长度4-20位';
    return false;
  }
  // 检查用户名是否已存在
  if (userList.value.some(item => item.username === username)) {
    addForm.value.usernameError = '用户名已存在';
    return false;
  }
  addForm.value.usernameError = '';
  return true;
};

// 验证角色选择
const validateRole = () => {
  if (!addForm.value.role_id) {
    addForm.value.roleError = '请选择角色';
    return false;
  }
  addForm.value.roleError = '';
  return true;
};

// 保存新增行（含角色）
const saveAddRow = async () => {
  // 表单校验
  if (!validateUsername()) return;
  if (!validateRole()) return;
  if (!addForm.value.password) {
    alert('请输入密码');
    return;
  }
  if (addForm.value.password.length < 6) {
    alert('密码长度不能少于6位');
    return;
  }
  if (addForm.value.password !== addForm.value.confirmPassword) {
    alert('两次输入的密码不一致');
    return;
  }

  loading.value = true;
  try {
    const res = await request.post('/erp-users/add/', {
      username: addForm.value.username.trim(),
      password: addForm.value.password.trim(),
      role_id: addForm.value.role_id // 传递角色ID
    });

    if (res && res.code === 200) {
      alert('新增用户（含角色）成功！');
      hideAddRow();
      fetchUsers(currentPage.value, true); // 刷新列表
    } else {
      alert(`新增失败：${res.msg || '未知错误'}`);
    }
  } catch (error) {
    console.error('新增用户失败：', error);
    alert(`新增失败：${error.response?.data?.msg || error.message || '网络异常'}`);
  } finally {
    loading.value = false;
  }
};

// 切换密码编辑行
const toggleEditRow = (id) => {
  if (editId.value === id) {
    // 取消编辑
    editId.value = null;
    editForm.value = { password: '', confirmPassword: '' };
  } else {
    // 开始编辑
    editId.value = id;
    editForm.value = { password: '', confirmPassword: '' };
    // 滚动到当前行
    scrollToRow(id);
  }
};

// 切换角色编辑行
const toggleEditRoleRow = async (id) => {
  if (editRoleId.value === id) {
    // 取消编辑
    editRoleId.value = null;
    editRoleForm.value = { role_id: '' };
  } else {
    // 先加载角色列表
    await fetchRoles();
    // 开始编辑
    editRoleId.value = id;
    // 回显当前角色
    const user = userList.value.find(item => item.id === id);
    if (user && user.role_id) {
      editRoleForm.value.role_id = user.role_id;
    } else {
      editRoleForm.value.role_id = '';
    }
    // 滚动到当前行
    scrollToRow(id);
  }
};

// 滚动到指定行
const scrollToRow = (id) => {
  setTimeout(() => {
    const row = document.querySelector(`.table-row:nth-child(${[...document.querySelectorAll('.table-row')].findIndex(el => el.querySelector('.col-id').textContent == id) + (addRowVisible.value ? 2 : 1)})`);
    if (row) row.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 100);
};

// 保存用户信息（密码/角色）
const saveUserInfo = async (id) => {
  loading.value = true;
  try {
    // 区分保存类型：密码/角色
    if (editId.value === id) {
      // 保存密码
      if (!editForm.value.password) {
        alert('请输入新密码');
        loading.value = false;
        return;
      }
      if (editForm.value.password.length < 6) {
        alert('密码长度不能少于6位');
        loading.value = false;
        return;
      }
      if (editForm.value.password !== editForm.value.confirmPassword) {
        alert('两次输入的密码不一致');
        loading.value = false;
        return;
      }

      const res = await request.put(`/erp-users/update/${id}/`, {
        password: editForm.value.password.trim()
      });

      if (res && res.code === 200) {
        alert('密码修改成功！');
        editId.value = null;
        editForm.value = { password: '', confirmPassword: '' };
      } else {
        alert(`密码修改失败：${res.msg || '未知错误'}`);
      }
    }

    if (editRoleId.value === id) {
      // 保存角色
      if (!editRoleForm.value.role_id) {
        alert('请选择角色');
        loading.value = false;
        return;
      }

      const res = await request.put(`/erp-users/update-role/${id}/`, {
        role_id: editRoleForm.value.role_id
      });

      if (res && res.code === 200) {
        alert('角色分配成功！');
        editRoleId.value = null;
        editRoleForm.value = { role_id: '' };
      } else {
        alert(`角色分配失败：${res.msg || '未知错误'}`);
      }
    }

    // 刷新用户列表
    fetchUsers(currentPage.value, true);
  } catch (error) {
    console.error('保存用户信息失败：', error);
    alert(`保存失败：${error.response?.data?.msg || error.message || '网络异常'}`);
  } finally {
    loading.value = false;
  }
};

// 获取用户列表（含角色信息）
const fetchUsers = async (page = 1, forceRefresh = false) => {
  if (loading.value) return;

  const now = Date.now();
  // 登录状态校验
  const isLogin = localStorage.getItem('erp_username');
  if (!isLogin || forceRefresh) {
    cache.value = { data: [], time: 0, page: 1 };
  }
  // 缓存逻辑
  if (!forceRefresh && cache.value.time + CACHE_DURATION > now && cache.value.page === page) {
    userList.value = cache.value.data;
    totalCount.value = cache.value.total;
    totalPages.value = cache.value.totalPages;
    currentPage.value = page;
    jumpPage.value = page;
    loading.value = false;
    return;
  }

  loading.value = true;
  userList.value = [];
  emptyMsg.value = '暂无用户数据，请先录入！';

  try {
    const reqPage = Number(page) || 1;
    const reqPageSize = Number(pageSize.value) || 10;

    const res = await request.get('/erp-users/', {
      params: {
        page: reqPage,
        page_size: reqPageSize,
        keyword: '',
        ...(forceRefresh ? { _t: now } : {})
      },
      timeout: 3000,
    });

    if (res && res.code === 200) {
      userList.value = res.data.list || [];
      totalCount.value = res.data.total || 0;
      currentPage.value = reqPage;
      totalPages.value = Math.ceil(totalCount.value / reqPageSize) || 1;
      jumpPage.value = reqPage;
      // 更新缓存
      cache.value = {
        data: userList.value,
        time: now,
        page: reqPage,
        total: totalCount.value,
        totalPages: totalPages.value
      };
    } else {
      emptyMsg.value = `接口返回异常：${res.msg || '无返回信息'}`;
    }
  } catch (error) {
    console.error('请求失败：', error);
    if (error.message.includes('Network Error')) {
      emptyMsg.value = '无法连接后端：请检查8000端口是否启动，或配置跨域！';
    } else if (error.code === 'ECONNABORTED') {
      emptyMsg.value = '请求超时：后端响应过慢，请检查服务！';
    } else if (error.response) {
      if (error.response.status === 401) {
        emptyMsg.value = '登录状态失效，请重新登录！';
        setTimeout(() => router.push('/login'), 1500);
      } else if (error.response.status === 404) {
        emptyMsg.value = `接口不存在 [404]：请检查后端是否配置/api/erp-users/路由`;
      } else {
        emptyMsg.value = `后端错误 [${error.response.status}]：${error.response.data?.msg || '未知错误'}`;
      }
    } else {
      emptyMsg.value = '加载失败：' + (error.message || '未知错误');
    }
  } finally {
    loading.value = false;
  }
};

// 单个删除用户（含角色关联删除）
const handleSingleDelete = async (id) => {
  const user = userList.value.find(item => item.id === id);
  if (!user) return;

  const confirmDelete = confirm(`确定删除用户【${user.username}】及其角色关联吗？删除后不可恢复！`);
  if (!confirmDelete) return;

  loading.value = true;
  try {
    const res = await request.delete(`/erp-users/delete/${id}/`);
    if (res && res.code === 200) {
      alert('删除用户成功！');
      fetchUsers(currentPage.value, true);
    } else {
      alert(`删除失败：${res.msg || '未知错误'}`);
    }
  } catch (error) {
    console.error('删除用户失败：', error);
    alert(`删除失败：${error.response?.data?.msg || error.message || '网络异常'}`);
  } finally {
    loading.value = false;
  }
};

// 批量删除用户
const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return;

  const confirmDelete = confirm(`确定删除选中的${selectedIds.value.length}条用户及其角色关联吗？删除后不可恢复！`);
  if (!confirmDelete) return;

  loading.value = true;
  let successCount = 0;
  let failCount = 0;
  const failIds = [];

  try {
    const deletePromises = selectedIds.value.map(async (id) => {
      try {
        await request.delete(`/erp-users/delete/${id}/`);
        return { id, success: true };
      } catch (err) {
        return { id, success: false };
      }
    });

    const results = await Promise.all(deletePromises);
    results.forEach(result => {
      if (result.success) {
        successCount++;
      } else {
        failCount++;
        failIds.push(result.id);
      }
    });

    let tipMsg = '';
    if (successCount > 0 && failCount === 0) {
      tipMsg = `成功删除${successCount}条用户！`;
    } else if (successCount > 0 && failCount > 0) {
      tipMsg = `成功删除${successCount}条，失败${failCount}条（失败ID：${failIds.join(',')}）！`;
    } else {
      tipMsg = `删除失败：所有选中的${failCount}条用户都未能删除！`;
    }
    alert(tipMsg);

    if (successCount > 0) {
      fetchUsers(currentPage.value, true);
      allChecked.value = false;
      selectedIds.value = [];
    }
  } catch (err) {
    alert(`批量删除异常：${err.message}`);
    console.error('批量删除失败：', err);
  } finally {
    loading.value = false;
  }
};

// 防抖刷新（同时刷新用户和角色）
const handleRefresh = debounce(async () => {
  await fetchRoles(true); // 强制刷新角色
  fetchUsers(currentPage.value, true); // 强制刷新用户
}, 200);

// 分页切换防抖
const changePage = debounce((page) => {
  if (page < 1 || page > totalPages.value || loading.value) return;
  fetchUsers(page);
}, 100);

// 页码跳转防抖
const jumpToPage = debounce(() => {
  changePage(jumpPage.value);
}, 100);

// 路由监听
const routeWatchHandler = debounce(async (newPath) => {
  if (newPath.includes('/layout/system/erp-user')) {
    await fetchRoles(); // 先加载角色
    fetchUsers(currentPage.value);
  }
}, 100);

watch(
  () => route.fullPath,
  routeWatchHandler,
  { immediate: true, deep: true }
);

// 组件挂载
onMounted(async () => {
  console.log('用户管理组件挂载完成，开始加载数据');
  const isLogin = localStorage.getItem('erp_username');
  if (!isLogin) {
    alert('请先登录系统！');
    router.push('/login');
    return;
  }
  await fetchRoles(); // 先加载角色列表
  fetchUsers();
  window.__forceFetchERPUsers = fetchUsers;
  window.__forceFetchERPRoles = fetchRoles;
});

// 组件卸载
onUnmounted(() => {
  delete window.__forceFetchERPUsers;
  delete window.__forceFetchERPRoles;
  cache.value = { data: [], time: 0, page: 1 };
  roleCache.value = { data: [], time: 0 };
});
</script>

<style scoped>
/* 基础样式复用原有，新增角色相关样式 */
.erp-user-management {
  margin: 24px auto;
  padding: 24px 32px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  max-width: 1600px;
  width: 98%;
  box-sizing: border-box;
  position: relative;
  min-height: 600px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-header h4 {
  font-size: 18px;
  color: #0c4a6e;
  margin: 0;
}

.add-btn, .refresh-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.add-btn {
  background: #10b981;
  transition: background 0.2s ease;
}

.add-btn:hover {
  background: #059669;
}

.add-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
}

/* 刷新按钮样式 */
.refresh-btn {
  background: #0ea5e9;
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  padding: 0;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  background: #0284c7;
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
}

/* 批量删除按钮样式 */
.delete-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  background: #ef4444;
  margin-left: 12px;
  font-size: 14px;
  transition: background 0.2s ease;
}

.delete-btn:hover {
  background: #dc2626;
}

.delete-btn:disabled {
  background: #fca5a5;
  cursor: not-allowed;
}

/* 骨架屏样式（适配新增角色列） */
.skeleton-container {
  width: 100%;
  padding: 12px 0;
}

.skeleton-row {
  display: flex;
  height: 44px;
  margin-bottom: 10px;
  align-items: center;
}

.skeleton-col {
  background: linear-gradient(90deg, #f0f9ff 25%, #e0f2fe 50%, #f0f9ff 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  height: 28px;
}

/* 调整骨架列宽，新增角色列 */
.skeleton-col.col-checkbox { width: 6%; margin: 0 6px; }
.skeleton-col.col-id { width: 8%; margin: 0 6px; }
.skeleton-col.col-name { width: 18%; margin: 0 6px; }
.skeleton-col.col-role { width: 18%; margin: 0 6px; }
.skeleton-col.col-password { width: 18%; margin: 0 6px; }
.skeleton-col.col-confirm { width: 18%; margin: 0 6px; }
.skeleton-col.col-actions { width: 18%; margin: 0 6px; }

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 复选框列样式 */
.col-checkbox {
  width: 6%;
  text-align: center;
  padding: 16px 10px;
}

.check-all, .check-row {
  width: 24px;
  height: 24px;
  cursor: pointer;
  margin: 0 auto;
  position: relative;
}

.check-all::after, .check-row::after {
  content: '';
  position: absolute;
  top: -6px;
  left: -6px;
  right: -6px;
  bottom: -6px;
}

.check-all:disabled, .check-row:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* 选中数量提示 */
.selected-count {
  color: #ef4444;
  margin-left: 14px;
  font-weight: 600;
  font-size: 14px;
}

.loading, .empty {
  text-align: center;
  padding: 60px 0;
  color: #64748b;
  font-size: 16px;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
  min-height: 300px;
  margin: 12px 0;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.material-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.material-table th {
  background: #f0f9ff;
  color: #0c4a6e;
  font-weight: 600;
  padding: 16px 10px;
  font-size: 15px;
  border-bottom: 2px solid #bae6fd;
  white-space: nowrap;
}

.material-table td {
  padding: 16px 10px;
  font-size: 14px;
  color: #334155;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.table-row {
  cursor: default;
  transition: background 0.2s ease;
}

.table-row:hover {
  background: #e0f2fe;
}

/* 新增行样式 */
.add-row {
  background: #fef7fb;
}

.add-row:hover {
  background: #fef7fb;
}

/* 编辑输入框/下拉框样式 */
.edit-input, .edit-select {
  width: 90%;
  padding: 8px 10px;
  border: 1px solid #0ea5e9;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.edit-input:focus, .edit-select:focus {
  outline: none;
  border-color: #0284c7;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}

/* 错误提示 */
.error-tip {
  display: block;
  font-size: 12px;
  color: #ef4444;
  margin-top: 4px;
  padding-left: 2px;
}

/* 编辑提示 */
.edit-tip {
  font-size: 12px;
  color: #0ea5e9;
}

/* 调整表格列宽，新增角色列 */
.col-id { width: 8%; text-align: center; }
.col-name { width: 18%; text-align: left; padding-left: 20px; }
.col-role { width: 18%; text-align: left; padding-left: 20px; }
.col-password { width: 18%; text-align: left; padding-left: 20px; }
.col-confirm { width: 18%; text-align: left; padding-left: 20px; }
.col-actions { width: 18%; text-align: center; }

/* 操作按钮样式 */
.edit-btn, .role-btn, .save-btn, .cancel-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin: 0 4px;
  transition: all 0.2s ease;
}

.edit-btn {
  background: #f1f5f9;
  color: #0c4a6e;
}

.edit-btn:hover {
  background: #e0f2fe;
}

/* 角色操作按钮样式 */
.role-btn {
  background: #f0f9ff;
  color: #0ea5e9;
}

.role-btn:hover {
  background: #bae6fd;
}

.save-btn {
  background: #10b981;
  color: #fff;
}

.save-btn:hover {
  background: #059669;
}

.save-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
}

.cancel-btn {
  background: #ef4444;
  color: #fff;
}

.cancel-btn:hover {
  background: #dc2626;
}

/* admin标签样式 */
.admin-tag {
  display: inline-block;
  padding: 2px 6px;
  background: #f0f9ff;
  color: #0ea5e9;
  font-size: 12px;
  border-radius: 4px;
  margin-left: 8px;
}

/* 不可操作文本 */
.disabled-text {
  color: #94a3b8;
  font-size: 12px;
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
  font-size: 15px;
  color: #64748b;
  padding-right: 70px;
  box-sizing: border-box;
}

.pagination-info {
  display: flex;
  align-items: center;
}

.pagination-btns {
  display: flex;
  gap: 10px;
  align-items: center;
}

.page-btn {
  padding: 6px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: #e0f2fe;
  border-color: #0ea5e9;
}

.page-btn:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.page-jump input {
  width: 70px;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
}

.jump-btn {
  padding: 6px 14px;
  background: #0ea5e9;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.jump-btn:hover:not(:disabled) {
  background: #0284c7;
}

.jump-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 大屏适配 */
@media (min-width: 1920px) {
  .erp-user-management {
    max-width: 1800px;
    padding: 32px 40px;
  }
  .material-table th, .material-table td {
    padding: 18px 12px;
    font-size: 15px;
  }
  .skeleton-row {
    height: 48px;
  }
  .skeleton-col {
    height: 32px;
  }
}

/* 中等屏幕适配 */
@media (max-width: 1440px) {
  .erp-user-management {
    max-width: 1400px;
    width: 95%;
  }
}

/* 小屏幕适配 */
@media (max-width: 768px) {
  .pagination {
    flex-direction: column;
    gap: 14px;
    align-items: flex-start;
    padding-right: 0;
  }
  .pagination-btns {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .material-table th, .material-table td {
    padding: 12px 6px;
    font-size: 13px;
  }
  .col-checkbox { width: 10%; }
  .skeleton-col.col-checkbox { width: 10%; }
  .refresh-btn {
    bottom: 18px;
    right: 18px;
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  .erp-user-management {
    max-width: 100%;
    padding: 16px;
    margin: 16px auto;
    width: calc(100% - 32px);
  }
}

/* 移动端适配 */
@media (max-width: 480px) {
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  .header-actions {
    width: 100%;
    display: flex;
    gap: 10px;
  }
  .add-btn, .delete-btn {
    flex: 1;
    width: 100%;
    padding: 10px;
  }
  .pagination-btns {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }
  .col-checkbox { width: 12%; }
  .skeleton-col.col-checkbox { width: 12%; }
  .erp-user-management {
    padding: 12px;
    margin: 8px auto;
    width: calc(100% - 16px);
    min-height: 500px;
  }
  /* 移动端调整列宽 */
  .col-id { width: 10%; }
  .col-name { width: 16%; }
  .col-role { width: 16%; }
  .col-password { width: 16%; }
  .col-confirm { width: 16%; }
  .col-actions { width: 24%; }
  /* 移动端按钮换行 */
  .col-actions .edit-btn,
  .col-actions .role-btn,
  .col-actions .save-btn,
  .col-actions .delete-btn {
    display: block;
    margin: 4px auto;
    width: 90%;
  }
}
</style>